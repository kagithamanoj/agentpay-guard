import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import parse_deterministic


def test_full_sentence():
    r = parse_deterministic("buy 2 wireless mice from Acme Supplies for $84")
    assert r.vendor == "Acme Supplies"
    assert r.quantity == 2
    assert r.amount_usd == 84.0
    assert "wireless mice" in r.item


def test_no_quantity_defaults_to_one():
    r = parse_deterministic("order a docking station from Dell for $129.99")
    assert r.quantity == 1
    assert r.amount_usd == 129.99


def test_missing_amount_raises():
    try:
        parse_deterministic("buy a mouse from Dell")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_gift_card_category_detected():
    r = parse_deterministic("buy a $50 gift card from Amazon for $50")
    assert r.category == "gift card"
