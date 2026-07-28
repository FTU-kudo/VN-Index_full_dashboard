# FILE: tests/test_client.py
from __future__ import annotations
import pytest
import responses
import requests
from src.data.yuanta_client import YuantaAPIClient

MOCK_PRICE_RESPONSE = {
    "success": True,
    "response": [{
        "StockCode": "ACB", "Exchange": "HSX", "SymbolType": "ST",
        "RefP": 22500, "CeilingP": 24050, "FloorP": 20950,
        "HighestP": 22650, "LowestP": 22100, "OpenP": 22100,
        "AvgP": 22462.74, "LastMP": 22500, "LastMVol": 300,
        "DeemP": 22500, "DeemVol": 1885300,
        "TotalVol": 13447000, "TotalVal": 302056465000,
        "FTBuyVol": 1493401, "FTSellVol": 3534613,
        "FTBuyVal": 33469717300, "FTSellVal": 79410314900,
        "FRoom": 313720186,
        "SymbolAdminStatusCode": "NRM", "ExClassType": "00",
        "S1P": 22550, "S1V": 30600, "S2P": 22600, "S2V": 69900,
        "S3P": 22650, "S3V": 277300,
        "B1P": 22500, "B1V": 93500, "B2P": 22450, "B2V": 59400,
        "B3P": 22400, "B3V": 147400
    }],
    "error": None
}

@responses.activate
def test_yuanta_client_get_success():
    client = YuantaAPIClient()
    url = "https://ysradarapi.yuanta.com.vn/api/v3/market_data/price_board/stock/list_stock_info"
    responses.add(
        responses.GET,
        url,
        json=MOCK_PRICE_RESPONSE,
        status=200
    )
    
    resp = client.get("market_data/price_board/stock/list_stock_info", params={"stock_list": "ACB", "stock_type": "ST"})
    
    assert resp["success"] is True
    assert len(resp["response"]) == 1
    assert resp["response"][0]["StockCode"] == "ACB"
    assert resp["response"][0]["LastMP"] == 22500

@responses.activate
def test_yuanta_client_retry_on_429():
    client = YuantaAPIClient()
    url = "https://ysradarapi.yuanta.com.vn/api/v3/test_retry"
    
    # Mock two 429 failures, then a 200 success
    responses.add(responses.GET, url, json={"error": "Rate limit"}, status=429)
    responses.add(responses.GET, url, json={"error": "Rate limit"}, status=429)
    responses.add(responses.GET, url, json={"success": True, "data": "OK"}, status=200)
    
    resp = client.get("test_retry")
    assert resp["success"] is True
    assert len(responses.calls) == 3

@responses.activate
def test_yuanta_client_404_error():
    client = YuantaAPIClient()
    url = "https://ysradarapi.yuanta.com.vn/api/v3/test_404"
    
    responses.add(responses.GET, url, status=404)
    
    with pytest.raises(requests.exceptions.HTTPError):
        client.get("test_404")
