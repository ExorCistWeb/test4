
### `variant-1/src/service.py`
import requests
import json
from typing import Dict, Any

class PaymentService:
    def __init__(self, gateway_url: str = "https://api.payments.example/v1/charge"):
        self.gateway_url = gateway_url

    def process_payment(self, amount: float, card_token: str) -> Dict[str, Any]:
        payload = {
            "amount": amount,
            "currency": "RUB",
            "card_token": card_token
        }
        try:
            response = requests.post(
                self.gateway_url,
                json=payload,
                headers={"Content-Type": "application/json", "Authorization": "Bearer sk_test_123"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return {"success": True, "tx_id": data.get("tx_id")}
            else:
                return {"success": False, "error": data.get("reason", "unknown")}
        except requests.Timeout:
            return {"success": False, "error": "timeout"}
        except requests.RequestException:
            return {"success": False, "error": "network_error"}