"""Policy engine for AgentPay Guard.

Decides whether an agent purchase request can proceed, must be held
for a human, or is blocked outright. Fails closed: anything unusual
is held or blocked, never auto-approved.
"""
from dataclasses import dataclass, field

AUTO_APPROVE_CAP_USD = 100.00

ALLOWED_VENDORS = {
    "acme supplies",
    "amazon",
    "dell",
    "newegg",
    "staples",
}

BLOCKED_CATEGORIES = {
    "gift card",
    "gift cards",
    "crypto",
    "gambling",
    "alcohol",
}


@dataclass
class PurchaseRequest:
    vendor: str
    item: str
    quantity: int
    amount_usd: float
    category: str = ""


@dataclass
class PolicyDecision:
    action: str  # "approve", "hold", or "block"
    reasons: list = field(default_factory=list)


def evaluate(req: PurchaseRequest, recent: list | None = None) -> PolicyDecision:
    reasons = []
    vendor = req.vendor.strip().lower()
    category = req.category.strip().lower()

    if category in BLOCKED_CATEGORIES:
        return PolicyDecision("block", [f"blocked category: {category}"])
    if req.amount_usd <= 0:
        return PolicyDecision("block", ["amount must be positive"])

    if vendor not in ALLOWED_VENDORS:
        reasons.append(f"vendor not on allowlist: {req.vendor}")
    if req.amount_usd > AUTO_APPROVE_CAP_USD:
        reasons.append(
            f"amount ${req.amount_usd:.2f} over auto-approve cap ${AUTO_APPROVE_CAP_USD:.2f}"
        )
    for prior in recent or []:
        if (
            prior.vendor.strip().lower() == vendor
            and prior.item.strip().lower() == req.item.strip().lower()
            and abs(prior.amount_usd - req.amount_usd) < 0.01
        ):
            reasons.append("duplicate of a recent request")
            break

    if reasons:
        return PolicyDecision("hold", reasons)
    return PolicyDecision("approve", ["within cap, allowlisted vendor"])
