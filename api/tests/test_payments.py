import pytest
from fastapi import status

def test_create_payment_intent_success(client, test_wallet_address, mock_payment_service):
    """Test successful payment intent creation."""
    payment_data = {
        "amount": 1000,  # $10.00
        "currency": "usd",
        "wallet_address": test_wallet_address
    }
    response = client.post(
        "/payments/create-intent",
        json=payment_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "client_secret" in data
    assert "payment_intent_id" in data

def test_create_payment_intent_invalid_amount(client, test_wallet_address):
    """Test payment intent creation with invalid amount."""
    payment_data = {
        "amount": -1000,  # Invalid negative amount
        "currency": "usd",
        "wallet_address": test_wallet_address
    }
    response = client.post(
        "/payments/create-intent",
        json=payment_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_create_payment_intent_invalid_currency(client, test_wallet_address):
    """Test payment intent creation with invalid currency."""
    payment_data = {
        "amount": 1000,
        "currency": "invalid",  # Invalid currency
        "wallet_address": test_wallet_address
    }
    response = client.post(
        "/payments/create-intent",
        json=payment_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_payment_status_success(client, mock_payment_service):
    """Test successful payment status retrieval."""
    payment_intent_id = "test_payment_intent"
    response = client.get(f"/payments/{payment_intent_id}/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "amount" in data
    assert "currency" in data

def test_get_payment_status_not_found(client):
    """Test payment status retrieval with non-existent payment."""
    non_existent_payment = "non-existent-payment"
    response = client.get(f"/payments/{non_existent_payment}/status")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_create_subscription_success(client, test_wallet_address, mock_payment_service):
    """Test successful subscription creation."""
    subscription_data = {
        "plan_id": "premium",
        "wallet_address": test_wallet_address
    }
    response = client.post(
        "/subscriptions/create",
        json=subscription_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "subscription_id" in data
    assert "status" in data
    assert "plan_id" in data
    assert data["plan_id"] == "premium"

def test_create_subscription_invalid_plan(client, test_wallet_address):
    """Test subscription creation with invalid plan."""
    subscription_data = {
        "plan_id": "invalid_plan",
        "wallet_address": test_wallet_address
    }
    response = client.post(
        "/subscriptions/create",
        json=subscription_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_subscription_status_success(client, mock_payment_service):
    """Test successful subscription status retrieval."""
    subscription_id = "test_subscription"
    response = client.get(f"/subscriptions/{subscription_id}/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "plan_id" in data
    assert "current_period_end" in data

def test_get_subscription_status_not_found(client):
    """Test subscription status retrieval with non-existent subscription."""
    non_existent_subscription = "non-existent-subscription"
    response = client.get(f"/subscriptions/{non_existent_subscription}/status")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_cancel_subscription_success(client, mock_payment_service):
    """Test successful subscription cancellation."""
    subscription_id = "test_subscription"
    response = client.post(f"/subscriptions/{subscription_id}/cancel")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "cancelled"

def test_cancel_subscription_not_found(client):
    """Test subscription cancellation with non-existent subscription."""
    non_existent_subscription = "non-existent-subscription"
    response = client.post(f"/subscriptions/{non_existent_subscription}/cancel")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_list_available_plans_success(client, mock_payment_service):
    """Test successful plan listing."""
    response = client.get("/subscriptions/plans")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    for plan in data:
        assert "plan_id" in plan
        assert "name" in plan
        assert "price" in plan
        assert "features" in plan

def test_payment_webhook_success(client, mock_payment_service):
    """Test successful payment webhook handling."""
    webhook_data = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "test_payment_intent",
                "amount": 1000,
                "currency": "usd",
                "status": "succeeded"
            }
        }
    }
    response = client.post(
        "/payments/webhook",
        json=webhook_data
    )
    assert response.status_code == status.HTTP_200_OK

def test_payment_webhook_invalid_signature(client):
    """Test payment webhook with invalid signature."""
    webhook_data = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "test_payment_intent",
                "amount": 1000,
                "currency": "usd",
                "status": "succeeded"
            }
        }
    }
    # Add invalid signature header
    headers = {"Stripe-Signature": "invalid_signature"}
    response = client.post(
        "/payments/webhook",
        json=webhook_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST 