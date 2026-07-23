"""Integration tests: exercise the FastAPI app end-to-end (HTTP layer +
SQLite queries + response serialization) via TestClient.

The /analyze endpoint's call into the real LLM is mocked out so these
stay fast, free, and deterministic.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_classic.agents import AgentExecutor

import backend_main

client = TestClient(backend_main.app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_get_stock_data(fake_db):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert rows[0]["Company"] == "AAPL"


def test_get_stock_data_unknown_company_returns_empty_list(fake_db):
    response = client.get("/stocks/ZZZZ")
    assert response.status_code == 200
    assert response.json() == []


def test_get_sentiment_data(fake_db):
    response = client.get("/sentiment/AAPL")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["sentiment_label"] == "positive"


def test_analyze_endpoint_uses_agent_executor(fake_db):
    # AgentExecutor is a pydantic model, so its `invoke` method must be
    # patched on the class rather than the instance.
    fake_result = {"output": "AAPL looks strong based on recent trends."}
    with patch.object(AgentExecutor, "invoke", return_value=fake_result):
        response = client.get("/analyze/AAPL")
    assert response.status_code == 200
    assert response.json() == {"summary": fake_result["output"]}


def test_compare_endpoint_uses_agent_executor(fake_db):
    fake_result = {"output": "AAPL has stronger momentum than TSLA."}
    with patch.object(AgentExecutor, "invoke", return_value=fake_result) as mock_invoke:
        response = client.get("/compare", params={"a": "AAPL", "b": "TSLA"})
    assert response.status_code == 200
    assert response.json() == {"summary": fake_result["output"]}
    # The two tickers should reach the agent's input prompt.
    sent_input = mock_invoke.call_args.args[0]["input"]
    assert "AAPL" in sent_input
    assert "TSLA" in sent_input


def test_compare_endpoint_requires_both_params(fake_db):
    response = client.get("/compare", params={"a": "AAPL"})
    assert response.status_code == 422
