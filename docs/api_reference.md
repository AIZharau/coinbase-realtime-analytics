## REST Endpoints

### 1. Getting the last candles
GET /api/ohlc?product_id=BTC-USD&interval=1m&limit=100

Copy

Response:
```json
{
  "data": [
    {
      "time": "2023-11-15T12:34:00Z",
      "open": 42500.50,
      "high": 42580.75,
      "low": 42490.25,
      "close": 42520.00,
      "volume": 15.25
    }
  ]
}
```

### 2. Anomaly detection
```
GET /api/anomalies?threshold=5
```
Response:

```json
{
  "anomalies": [
    {
      "time": "2023-11-15T12:35:02Z",
      "product_id": "BTC-USD",
      "price_jump": 5.8,
      "volume_spike": 210.5
    }
  ]
}
```
WebSocket Stream
```
ws://<host>/api/stream
```
Sample message:

```json

{
  "event": "price_update",
  "data": {
    "product_id": "BTC-USD",
    "price": 42530.25,
    "timestamp": "2023-11-15T12:35:02Z"
  }
}
```