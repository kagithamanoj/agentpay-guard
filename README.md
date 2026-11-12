# AgentPay Guard

An AI agent that can buy things needs a guardrail before money moves, not after.

AgentPay Guard sits between an AI shopping agent and PayPal. The agent states a
purchase in plain language. A parser extracts vendor, item, quantity, and amount
(a local LLM via Ollama when available, with a deterministic fallback). A policy
engine then decides: approve, hold for a human, or block. Held purchases fail
closed until a human approves them. Approved purchases execute through the
PayPal Sandbox Orders v2 API, and every decision lands in an audit log.

Built for the PayPal AI Hackathon (deadline Nov 12, 2026). Solo project.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your PayPal sandbox Client ID and Secret
python3 app.py request "buy 2 wireless mice from Acme Supplies for $84"
python3 app.py request "buy a server from Dell for $450"   # held: over cap
python3 app.py capture <paypal_order_id>                    # after buyer approval
```

Without sandbox credentials the app runs in dry mode and prints the order
payload instead of calling PayPal. Dry mode is for development only.

## Policy defaults

- Auto-approve cap: $100 per order
- Vendor allowlist: Acme Supplies, Amazon, Dell, Newegg, Staples
- Blocked categories: gift cards, crypto, gambling, alcohol
- Duplicates of a recent request are held

## Tests

```bash
python3 -m pytest tests/ -q
```

## License

MIT
