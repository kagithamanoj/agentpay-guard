"""PayPal Sandbox Orders v2 client (stdlib + requests only).

Reads PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET from the environment.
Sandbox only: the base URL is fixed to the sandbox host on purpose.
"""
import os

import requests

BASE = "https://api-m.sandbox.paypal.com"


class PayPalSandbox:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or os.environ.get("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("PAYPAL_CLIENT_SECRET", "")
        self._token = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _access_token(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            BASE + "/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Content-Type": "application/json",
        }

    def create_order(self, amount_usd: float, description: str) -> dict:
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": description[:127],
                "amount": {"currency_code": "USD", "value": f"{amount_usd:.2f}"},
            }],
            "application_context": {
                "return_url": "https://example.com/return",
                "cancel_url": "https://example.com/cancel",
            },
        }
        resp = requests.post(BASE + "/v2/checkout/orders", json=payload,
                             headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def capture_order(self, order_id: str) -> dict:
        resp = requests.post(BASE + f"/v2/checkout/orders/{order_id}/capture",
                             headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def approve_link(order: dict) -> str | None:
        for link in order.get("links", []):
            if link.get("rel") == "approve":
                return link.get("href")
        return None
