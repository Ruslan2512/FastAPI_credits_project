import pytest
from fastapi.testclient import TestClient
from main import credits_app

client = TestClient(credits_app)


def test_get_user_credits():
    response = client.get("/user_credits/1")
    assert response.status_code == 200
    assert "issuance_date" in response.json()[0]


# def test_plans_insert():
#     with open("plans_test.xlsx", "rb") as file:
#         response = client.post("/plans_insert", files={"file": file})
#         assert response.status_code == 200
#         assert response.json() == {"detail": "Plans successfully added"}


def test_get_plans_performance():
    response = client.get("/plans_performance?date=2024-01-01")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if response.json():
        assert "plan_month" in response.json()[0]
        assert "performance_percent" in response.json()[0]
