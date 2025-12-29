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
from cs2_arb.scoring.opportunity import ScoreConfig, opportunity_score
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
    """End-to-end demo: load fixtures, compute GRP, rank listings."""
    s = Settings()
    cache = SqliteCache(s.cache_path)
    ecb = ECBRates(cache=cache, url=s.ecb_daily_url)
    _, rates = _load_rates(ecb, offline_fx)

    fees = {
        "steam": MarketFee(pct=s.fee_steam_pct),
        "buff163": MarketFee(pct=s.fee_buff_pct),
        "demo": MarketFee(pct=0.02),
    }

    m = DemoJSONMarket()
    pp = m.load_price_prints(prices)
    ls = m.load_listings(listings)

    prints_by_item = group_prints_by_item(pp)
    listings_by_item = group_listings_by_item(ls)

    rows = []
    for item_key, llist in listings_by_item.items():
        if item_key not in prints_by_item:
            continue
        grp = grp_for_item(
            prints=prints_by_item[item_key],
            ecb_rates=rates,
            fees_by_market=fees,
            cfg=GRPConfig(base_ccy=s.base_ccy),
        )
        for listing in llist:
            fee = fees.get(listing.market, MarketFee(pct=0.0))

            from cs2_arb.pricing.features import FeatureConfig, compute_model_price

            feats = ListingFeatures(
                float_value=listing.float_value,
                seed=listing.seed,
                stickers=None,  # listing.stickers parsing omitted for demo simplicity unless in JSON
            )

            # Compute Model Price
            model_price = compute_model_price(grp, feats, FeatureConfig())

            score = opportunity_score(
                listing=listing,
                reference_price_usd=model_price,
                ecb_rates=rates,
                fee=fee,
                cfg=ScoreConfig(base_ccy=s.base_ccy),
            )
            rows.append(
                (
                    score,
                    item_key,
                    listing.market,
                    listing.listing_id,
                    listing.ask,
                    listing.currency,
                    model_price,
                )
            )

    rows.sort(key=lambda x: x[0], reverse=True)

    t = Table(title=f"Top {top} opportunities (demo)")
    t.add_column("Score", justify="right")
    t.add_column("Item")
    t.add_column("Market")
    t.add_column("Listing")
    t.add_column("Ask")
    t.add_column("CCY")
    t.add_column("GRP_USD", justify="right")

    for score, item_key, market, listing_id, ask, ccy, grp in rows[:top]:
        t.add_row(
            str(score.quantize(Decimal("0.0001"))),
            item_key,
            market,
            listing_id,
            str(ask),
            ccy,
            str(grp.quantize(Decimal("0.01"))),
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
    if d and rates:  # Check if rates were loaded successfully
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
