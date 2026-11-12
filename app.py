"""AgentPay Guard demo CLI.

Flow: parse a plain-language purchase request, evaluate policy,
hold for a human when the policy says hold, and only then create a
PayPal Sandbox order. Without sandbox credentials it runs in dry
mode and prints the order payload instead of calling PayPal.
Dry mode is for development; the submission demo uses the sandbox.

Usage:
  python3 app.py request "buy 2 wireless mice from Acme Supplies for $84"
  python3 app.py capture <paypal_order_id>
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ENV = Path(__file__).parent / ".env"
if _ENV.exists():
    for _line in _ENV.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from parser import parse
from paypal_client import PayPalSandbox
from policy import evaluate

AUDIT_LOG = Path(__file__).parent / "audit_log.jsonl"
_recent: list = []


def audit(entry: dict) -> None:
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with AUDIT_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    print("audit:", json.dumps(entry))


def run_request(text: str) -> int:
    req = parse(text)
    decision = evaluate(req, recent=_recent)
    _recent.append(req)
    print(f"parsed: vendor={req.vendor!r} item={req.item!r} qty={req.quantity} amount=${req.amount_usd:.2f}")
    print(f"policy: {decision.action} ({'; '.join(decision.reasons)})")

    if decision.action == "block":
        audit({"event": "blocked", "vendor": req.vendor, "amount": req.amount_usd,
               "reasons": decision.reasons})
        return 0
    if decision.action == "hold":
        answer = input("HOLD: approve this purchase? [y/N] ").strip().lower()
        if answer != "y":
            audit({"event": "denied_by_human", "vendor": req.vendor,
                   "amount": req.amount_usd, "reasons": decision.reasons})
            print("Denied. No order created. Fails closed.")
            return 0
        audit({"event": "approved_by_human", "vendor": req.vendor, "amount": req.amount_usd})

    paypal = PayPalSandbox()
    description = f"{req.quantity} x {req.item} from {req.vendor}"
    if not paypal.configured:
        print("DRY RUN (no sandbox credentials): would create order:")
        print(json.dumps({"intent": "CAPTURE", "description": description,
                          "amount": {"currency_code": "USD", "value": f"{req.amount_usd:.2f}"}}, indent=2))
        audit({"event": "dry_run_order", "vendor": req.vendor, "amount": req.amount_usd})
        return 0

    order = paypal.create_order(req.amount_usd, description)
    print(f"PayPal sandbox order created: {order['id']}")
    print(f"Buyer approve link: {paypal.approve_link(order)}")
    print(f"After buyer approval, run: python3 app.py capture {order['id']}")
    audit({"event": "order_created", "vendor": req.vendor, "amount": req.amount_usd,
           "order_id": order["id"]})
    return 0


def run_capture(order_id: str) -> int:
    paypal = PayPalSandbox()
    if not paypal.configured:
        print("No sandbox credentials set; cannot capture.")
        return 1
    result = paypal.capture_order(order_id)
    print(f"Capture status: {result.get('status')} for order {order_id}")
    audit({"event": "order_captured", "order_id": order_id, "status": result.get("status")})
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "request":
        sys.exit(run_request(sys.argv[2]))
    if len(sys.argv) >= 3 and sys.argv[1] == "capture":
        sys.exit(run_capture(sys.argv[2]))
    print(__doc__)
    sys.exit(2)
