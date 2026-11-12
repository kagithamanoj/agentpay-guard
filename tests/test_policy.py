import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from policy import PurchaseRequest, evaluate


def req(**kw):
    base = dict(vendor="Acme Supplies", item="wireless mouse", quantity=2, amount_usd=84.0)
    base.update(kw)
    return PurchaseRequest(**base)


def test_small_allowlisted_approves():
    assert evaluate(req()).action == "approve"


def test_over_cap_holds():
    d = evaluate(req(amount_usd=450.0))
    assert d.action == "hold" and any("cap" in r for r in d.reasons)


def test_unknown_vendor_holds():
    d = evaluate(req(vendor="Random Storefront"))
    assert d.action == "hold"


def test_blocked_category_blocks():
    d = evaluate(req(item="gift card", category="gift card", amount_usd=50.0))
    assert d.action == "block"


def test_duplicate_holds():
    d = evaluate(req(), recent=[req()])
    assert d.action == "hold" and any("duplicate" in r for r in d.reasons)


def test_nonpositive_amount_blocks():
    assert evaluate(req(amount_usd=0)).action == "block"
