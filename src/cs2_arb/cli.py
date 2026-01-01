from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from cs2_arb.fx import ECBRates, implied_fx
from cs2_arb.markets.demo import DemoJSONMarket
from cs2_arb.models import ListingFeatures, MarketFee, PricePrint
from cs2_arb.pipeline import group_listings_by_item, group_prints_by_item
from cs2_arb.pricing.grp import GRPConfig, grp_for_item
from cs2_arb.scoring.routing import score_route
from cs2_arb.venue import VenueModel, FeeStructure
from cs2_arb.settings import Settings
from cs2_arb.storage.sqlite_cache import SqliteCache

app = typer.Typer(no_args_is_help=True)
console = Console()

demo_app = typer.Typer(no_args_is_help=True)
app.add_typer(demo_app, name="demo")


def _load_rates(ecb: ECBRates, offline_fx: str) -> tuple[datetime | None, dict[str, Decimal]]:
    """Try ECB cache/network, fall back to local JSON."""
    try:
        d, rates = ecb.latest()
        # convert date -> datetime for consistent type in UI messages
        return datetime(d.year, d.month, d.day, tzinfo=UTC), rates
    except Exception:
        with open(offline_fx, encoding="utf-8") as f:
            fx = json.load(f)
        d = datetime.fromisoformat(fx["date"]).replace(tzinfo=UTC)
        rates = {k: Decimal(v) for k, v in fx["rates"].items()}
        return d, rates


@demo_app.command("run")
def demo_run(
    prices: str = typer.Option(..., help="Path to demo price prints JSON"),
    listings: str = typer.Option(..., help="Path to demo listings JSON"),
    offline_fx: str = typer.Option("data/demo_ecb_rates.json", help="Offline FX fallback JSON"),
    top: int = typer.Option(15, help="How many rows to show"),
) -> None:
    """End-to-end demo: rank cross-venue Netback Routes."""
    s = Settings()
    cache = SqliteCache(s.cache_path)
    ecb = ECBRates(cache=cache, url=s.ecb_daily_url)
    _, rates = _load_rates(ecb, offline_fx)

    # Define Venues (simplified config for demo)
    venues = {
        "steam": VenueModel(
            name="steam",
            currency="USD", # Simplified
            buy_fee=FeeStructure(pct=0.0), 
            sell_fee=FeeStructure(pct=s.fee_steam_pct),
            settlement_days=7,
            risk_score=0.0
        ),
        "buff163": VenueModel(
            name="buff163",
            currency="CNY",
            buy_fee=FeeStructure(pct=0.0),
            sell_fee=FeeStructure(pct=s.fee_buff_pct),
            settlement_days=0,
            risk_score=0.05
        ),
        "demo": VenueModel(
            name="demo",
            currency="USD",
            buy_fee=FeeStructure(pct=0.0),
            sell_fee=FeeStructure(pct=0.02),
            settlement_days=0
        ),
    }

    m = DemoJSONMarket()
    pp = m.load_price_prints(prices)
    ls = m.load_listings(listings)

    prints_by_item = group_prints_by_item(pp)
    listings_by_item = group_listings_by_item(ls)

    routes = []
    
    # Pre-calculate best sell prices per market for each item
    # Map: item_key -> market -> price
    sell_prices: dict[str, dict[str, Decimal]] = {}
    for item_key, plist in prints_by_item.items():
        if item_key not in sell_prices:
            sell_prices[item_key] = {}
        # Naive: take the most recent print (or just average?)
        # For route arb, we want actionable liquidity. 
        # Using the last print is a proxy for "Market Price".
        for p in plist:
            # simple overwrite with latest if sorted? prints not strictly sorted in list
            # We'll assume list processing order or sort it.
            # Ideally we pick the latest by TS.
            current = sell_prices[item_key].get(p.market)
            # We don't have access to previous TS easily here without storing it.
            # Let's assume input prints are reasonably fresh or we just take the last one seen.
            # Better:
            sell_prices[item_key][p.market] = p.price

    for item_key, llist in listings_by_item.items():
        if item_key not in sell_prices:
            continue
            
        # Optional: Compute GRP for reference (not used for scoring anymore)
        fees_for_grp = {k: v.sell_fee for k, v in venues.items()}
        # Note: GRP config/calc might need MarketFee objects if strict, 
        # but FeeStructure is compatible duck-type (pct, fixed).
        
        for listing in llist:
            if listing.market not in venues:
                 continue
            
            buy_venue = venues[listing.market]
            
            # Identify route candidates
            possible_exits = sell_prices.get(item_key, {})
            
            for exit_market, exit_price in possible_exits.items():
                 if exit_market == listing.market:
                     continue
                 if exit_market not in venues:
                     continue
                 
                 sell_venue = venues[exit_market]
                 
                 # Score the route
                 route = score_route(
                     listing=listing,
                     buy_venue=buy_venue,
                     sell_venue=sell_venue,
                     sell_price_local=exit_price,
                     ecb_rates=rates,
                     implied_rates=None # Could add implied FX here
                 )
                 
                 routes.append(route)

    routes.sort(key=lambda x: x.score, reverse=True)

    t = Table(title=f"Top {top} Arbitrage Routes (Netback)")
    t.add_column("Score", justify="right")
    t.add_column("Item")
    t.add_column("Route")
    t.add_column("Input Cost ($)")
    t.add_column("Net Proceeds ($)")
    t.add_column("Edge %")

    for r in routes[:top]:
        t.add_row(
            f"{r.score:.2f}",
            r.item_key,
            f"{r.buy_venue} -> {r.sell_venue}",
            f"{r.buy_cost_usd:.2f}",
            f"{r.sell_proceeds_usd:.2f}",
            f"{r.roi_pct:.1f}%",
        )
    console.print(t)


features_app = typer.Typer(no_args_is_help=True)
app.add_typer(features_app, name="features")


@features_app.command("score-listing")
def features_score(
    base_price: str = typer.Option(..., help="Base GRP price (USD)"),
    float_val: str = typer.Option(..., help="Float value"),
    rarity: str = typer.Option("Mil-Spec", help="Item Category/Rarity"),
    seed: int | None = typer.Option(None, help="Pattern seed"),
    stickers_json: str | None = typer.Option(None, help="JSON string of stickers list"),
) -> None:
    """Compute the feature-adjusted model price for a hypothetical item."""
    import json

    from cs2_arb.pricing.features import FeatureConfig, compute_model_price

    base = Decimal(base_price)
    feats = ListingFeatures(
        float_value=float(float_val),
        seed=seed,
        stickers=json.loads(stickers_json) if stickers_json else None,
        rarity=rarity,
    )

    cfg = FeatureConfig()
    model = compute_model_price(base, feats, cfg)

    console.print(f"Base Price: ${base}")
    console.print(f"Rarity:     {rarity}")
    console.print(f"Float:      {float_val}")
    console.print(f"Model Price: ${model:.2f}")
    console.print(f"Multiplier: {model / base:.3f}x")


manufacturing_app = typer.Typer(no_args_is_help=True)
app.add_typer(manufacturing_app, name="manufacturing")


@manufacturing_app.command("analyze")
def manufacturing_analyze(
    input_prices: str = typer.Option(..., help="Comma-separated list of input GRP prices"),
    output_prices: str = typer.Option(..., help="Comma-separated list of output GRP prices"),
    rarity: str = typer.Option(
        "Mil-Spec", help="Rarity of INPUT items (e.g. 'Covert' uses 5 inputs, others 10)"
    ),
    ops_cost: str = typer.Option("0.50", help="Operational cost per contract"),
) -> None:
    """
    Analyze a trade-up contract profitability.
    Auto-detects input count based on rarity rules (5 for Red->Gold, 10 otherwise).
    """
    from cs2_arb.pricing.manufacturing import (
        calculate_input_cost,
        calculate_output_ev,
        manufacturing_edge,
    )

    inputs = [Decimal(x.strip()) for x in input_prices.split(",") if x.strip()]
    outputs_raw = [Decimal(x.strip()) for x in output_prices.split(",") if x.strip()]

    # Assume equal probability for outputs for this simple CLI demo
    outputs = [(p, 1.0 / len(outputs_raw)) for p in outputs_raw]

    cost = calculate_input_cost(inputs, input_rarity=rarity, ops_cost=Decimal(ops_cost))
    ev = calculate_output_ev(outputs)
    edge = manufacturing_edge(cost, ev)

    console.print(f"Rarity:     {rarity}")
    console.print(f"Input Cost: ${cost:.2f}")
    console.print(f"Output EV:  ${ev:.2f}")
    console.print(f"Edge:       ${edge:.2f}")


fx_app = typer.Typer(no_args_is_help=True)
app.add_typer(fx_app, name="fx")


@fx_app.command("update")
def fx_update() -> None:
    s = Settings()
    cache = SqliteCache(s.cache_path)
    ecb = ECBRates(cache=cache, url=s.ecb_daily_url)
    d, rates = ecb.update()
    console.print(f"Updated ECB rates for {d.isoformat()} with {len(rates)} currencies.")


@fx_app.command("show")
def fx_show(
    base: str = typer.Option("USD"),
    quote: str = typer.Option("CNY"),
    offline_fx: str = typer.Option("data/demo_ecb_rates.json", help="Offline FX fallback JSON"),
) -> None:
    s = Settings()
    cache = SqliteCache(s.cache_path)
    ecb = ECBRates(cache=cache, url=s.ecb_daily_url)
    d, rates = _load_rates(ecb, offline_fx)
    base = base.upper()
    quote = quote.upper()
    if base not in rates or quote not in rates:
        raise typer.BadParameter("Currency not in ECB table")
    # rates are EUR base:
    x = rates[quote] / rates[base]
    if d and rates:
        typer.echo(f"  Rate: 1 {base} = {x} {quote} (from {d.date()})")
    else:
        typer.echo(f"  Rate: 1 {base} = N/A {quote}")


@fx_app.command("implied")
def fx_implied(
    prices: str = typer.Option(..., help="Price prints JSON containing both currencies"),
    base: str = typer.Option("EUR", help="Base currency (numerator denominator base)"),
    quote: str = typer.Option("CNY", help="Quote currency"),
) -> None:
    """Estimate implied FX from a benchmark basket of cross-listed items."""
    m = DemoJSONMarket()
    pp = m.load_price_prints(prices)

    base = base.upper()
    quote = quote.upper()

    # For each item, take the most recent print in each currency
    latest_base: dict[str, PricePrint] = {}
    latest_quote: dict[str, PricePrint] = {}
    for p in pp:
        if p.currency.upper() == base:
            cur = latest_base.get(p.item_key)
            if cur is None or p.ts > cur.ts:
                latest_base[p.item_key] = p
        if p.currency.upper() == quote:
            cur = latest_quote.get(p.item_key)
            if cur is None or p.ts > cur.ts:
                latest_quote[p.item_key] = p

    pairs = []
    for k in set(latest_base.keys()) & set(latest_quote.keys()):
        pb = latest_base[k]
        pq = latest_quote[k]
        w = float(((pb.volume_7d or 1.0) + (pq.volume_7d or 1.0)) / 2.0) ** 0.5
        pairs.append((pb.price, pq.price, w))

    res = implied_fx(benchmark_pairs=pairs, base_ccy=base, quote_ccy=quote)
    console.print(f"Implied {base}->{quote}: 1 {base} ≈ {res.implied_rate} {quote} (n={res.n})")


grp_app = typer.Typer(no_args_is_help=True)
app.add_typer(grp_app, name="grp")


@grp_app.command("compute")
def grp_compute(
    prices: str = typer.Option(...),
    out: str | None = typer.Option(None, help="Write GRP table to JSON"),
    offline_fx: str = typer.Option("data/demo_ecb_rates.json", help="Offline FX fallback JSON"),
) -> None:
    s = Settings()
    cache = SqliteCache(s.cache_path)
    ecb = ECBRates(cache=cache, url=s.ecb_daily_url)
    _, rates = _load_rates(ecb, offline_fx)

    # Use simplified venues config for fees
    fees = {
        "steam": MarketFee(pct=s.fee_steam_pct),
        "buff163": MarketFee(pct=s.fee_buff_pct),
        "demo": MarketFee(pct=0.02),
    }

    m = DemoJSONMarket()
    pp = m.load_price_prints(prices)
    prints_by_item = group_prints_by_item(pp)

    now = datetime.now(UTC)
    out_rows = []
    for item_key, plist in prints_by_item.items():
        grp = grp_for_item(
            prints=plist,
            ecb_rates=rates,
            fees_by_market=fees,
            cfg=GRPConfig(base_ccy=s.base_ccy),
            now=now,
        )
        out_rows.append({"item_key": item_key, "ts": now.isoformat(), "grp_usd": str(grp)})

    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(out_rows, f, indent=2, sort_keys=True)
        console.print(f"Wrote {len(out_rows)} GRP points to {out}")
    else:
        console.print(out_rows[:5])
