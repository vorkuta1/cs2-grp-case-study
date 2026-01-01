from decimal import Decimal

from cs2_arb.pricing.manufacturing import (
    calculate_input_cost,
    calculate_output_ev,
    manufacturing_edge,
)


def test_input_cost() -> None:
    # 10 items at 10.00 each use default (Mil-Spec -> 10)
    inputs = [Decimal("10.00")] * 10
    cost = calculate_input_cost(inputs, input_rarity="Mil-Spec", ops_cost=Decimal("0.50"))
    assert cost == Decimal("100.50")


def test_input_cost_covert() -> None:
    # 5 items at 100.00 each for Covert -> Gold
    inputs = [Decimal("100.00")] * 5
    cost = calculate_input_cost(inputs, input_rarity="Covert", ops_cost=Decimal("0.50"))
    assert cost == Decimal("500.50")


def test_output_ev() -> None:
    # 50% chance of 50.00, 50% chance of 10.00
    outputs = [(Decimal("50.00"), 0.5), (Decimal("10.00"), 0.5)]
    ev = calculate_output_ev(outputs)
    # 25 + 5 = 30
    assert ev == Decimal("30.00")


def test_manufacturing_edge() -> None:
    cost = Decimal("100.00")
    ev = Decimal("120.00")
    edge = manufacturing_edge(cost, ev)
    assert edge == Decimal("20.00")
