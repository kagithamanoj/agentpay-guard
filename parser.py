"""Extract a PurchaseRequest from a plain-language agent request.

Deterministic parser is the default so the demo never depends on a
model being up. If OLLAMA_HOST is set, a local model can be used for
extraction instead; any failure falls back to this parser.
"""
import json
import os
import re
import urllib.request

from policy import PurchaseRequest

_AMOUNT = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")
_QTY_ITEM = re.compile(r"(?:buy|order|purchase)\s+(?:(\d+)\s+)?(.+?)\s+from\s+", re.I)
_FROM_VENDOR = re.compile(r"from\s+(.+?)(?:\s+for\s+|\s*$)", re.I)


def parse_deterministic(text: str) -> PurchaseRequest:
    amount_match = _AMOUNT.search(text)
    if not amount_match:
        raise ValueError("no $ amount found in request")
    amount = float(amount_match.group(1))

    vendor_match = _FROM_VENDOR.search(text)
    vendor = vendor_match.group(1).strip() if vendor_match else "unknown"

    item_match = _QTY_ITEM.search(text)
    if item_match:
        quantity = int(item_match.group(1)) if item_match.group(1) else 1
        item = item_match.group(2).strip()
    else:
        quantity, item = 1, "unspecified item"

    category = ""
    lowered = text.lower()
    for word in ("gift card", "gift cards"):
        if word in lowered:
            category = word
            break

    return PurchaseRequest(
        vendor=vendor, item=item, quantity=quantity,
        amount_usd=amount, category=category,
    )


def parse_with_ollama(text: str, host: str, model: str = "llama3.2:latest") -> PurchaseRequest:
    prompt = (
        "Extract vendor, item, quantity, amount_usd from this purchase request. "
        "Reply with JSON only.\nRequest: " + text
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    fields = json.loads(data["response"])
    return PurchaseRequest(
        vendor=str(fields["vendor"]), item=str(fields["item"]),
        quantity=int(fields.get("quantity", 1)),
        amount_usd=float(fields["amount_usd"]),
    )


def parse(text: str) -> PurchaseRequest:
    host = os.environ.get("OLLAMA_HOST")
    if host:
        try:
            return parse_with_ollama(text, host)
        except Exception:
            pass  # fail over to the deterministic parser, never fail the demo
    return parse_deterministic(text)
