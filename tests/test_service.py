import pytest
from unittest.mock import patch, Mock
from src.service import PaymentService
import requests
from json import JSONDecodeError



# 1. УСПЕШНЫЙ СЦЕНАРИЙ

def test_process_payment_success():
    service = PaymentService()

    mock_response = Mock()
    mock_response.json.return_value = {"status": "success", "tx_id": "txn_123"}
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(150.0, "tok_visa_9999")

        assert result["success"] is True
        assert result["tx_id"] == "txn_123"

        mock_post.assert_called_once()

        args, kwargs = mock_post.call_args
        assert args[0] == service.gateway_url

        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"] == {
            "amount": 150.0,
            "currency": "RUB",
            "card_token": "tok_visa_9999",
        }



# 2. ОТКАЗ БАНКА

def test_process_payment_failure():
    service = PaymentService()

    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "failure",
        "reason": "insufficient_funds"
    }
    mock_response.raise_for_status.return_value = None

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(100.0, "tok_fail")

        assert result["success"] is False
        assert result["error"] == "insufficient_funds"



# 3. ТАЙМАУТ

def test_process_payment_timeout():
    service = PaymentService()

    with patch("requests.post", side_effect=requests.Timeout):
        result = service.process_payment(200.0, "tok_timeout")

        assert result["success"] is False
        assert result["error"] == "timeout"



# 4. СЕТЕВАЯ ОШИБКА

def test_process_payment_network_error():
    service = PaymentService()

    with patch("requests.post", side_effect=requests.ConnectionError):
        result = service.process_payment(300.0, "tok_network")

        assert result["success"] is False
        assert result["error"] == "network_error"



# 5. HTTP-500

def test_process_payment_http_500():
    service = PaymentService()

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Server error")

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(120.0, "tok_err500")

        assert result["success"] is False
        assert result["error"] == "network_error"



# 6. HTTP-400

def test_process_payment_http_400():
    service = PaymentService()

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Bad request")

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(1.0, "bad_token")

        assert result["success"] is False
        assert result["error"] == "network_error"



# 7. ПУСТОЙ JSON

def test_process_payment_empty_json():
    service = PaymentService()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(90.0, "tok_empty")

        assert result["success"] is False
        assert result["error"] == "unknown"



# 8. НЕИЗВЕСТНЫЙ СТАТУС

def test_process_payment_unknown_status():
    service = PaymentService()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "strange_value"}

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        result = service.process_payment(50.0, "tok_weird")

        assert result["success"] is False
        assert result["error"] == "unknown"



# 9. Проверка тела запроса

def test_process_payment_request_body():
    service = PaymentService()

    mock_response = Mock()
    mock_response.json.return_value = {"status": "success", "tx_id": "id123"}
    mock_response.raise_for_status.return_value = None

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        service.process_payment(777.0, "tok_test")

        _, kwargs = mock_post.call_args

        assert kwargs["json"]["amount"] == 777.0
        assert kwargs["json"]["card_token"] == "tok_test"
        assert kwargs["json"]["currency"] == "RUB"



# 10. Проверка заголовков

def test_process_payment_request_headers():
    service = PaymentService()

    mock_response = Mock()
    mock_response.json.return_value = {"status": "success", "tx_id": "ok"}
    mock_response.raise_for_status.return_value = None

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        service.process_payment(10, "tok_hdr")

        _, kwargs = mock_post.call_args

        assert kwargs["headers"]["Authorization"] == "Bearer sk_test_123"
        assert kwargs["headers"]["Content-Type"] == "application/json"



# 11. Проверка URL

def test_process_payment_request_url():
    service = PaymentService(gateway_url="https://custom.url/pay")

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "success", "tx_id": "tx55"}

    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response

        service.process_payment(1, "tok_url")

        args, _ = mock_post.call_args

        assert args[0] == "https://custom.url/pay"
