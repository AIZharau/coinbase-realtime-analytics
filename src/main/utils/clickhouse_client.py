from clickhouse_driver import Client
from typing import Dict
from retry import retry
from utils.logging import setup_logging

logger = setup_logging(__name__)

class ClickHouseClient:
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self._connect()

    @retry(tries=3, delay=2, backoff=2)
    def _connect(self):
        try:
            self.client = Client(**self.config)
            logger.info("ClickHouse connection established")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def insert_raw_trade(self, data: Dict):
        try:
            self.client.execute(
                """
                INSERT INTO coinbase_market_data.raw_trades (
                    type, sequence, product_id, price, open_24h,
                    volume_24h, low_24h, high_24h, volume_30d,
                    best_bid, best_bid_size, best_ask, best_ask_size,
                    side, time, trade_id, last_size
                ) VALUES (
                    %(type)s, %(sequence)s, %(product_id)s, %(price)s, %(open_24h)s,
                    %(volume_24h)s, %(low_24h)s, %(high_24h)s, %(volume_30d)s,
                    %(best_bid)s, %(best_bid_size)s, %(best_ask)s, %(best_ask_size)s,
                    %(side)s, %(time)s, %(trade_id)s, %(last_size)s  # Убрали toDateTime()
                )
                """,
                data
            )
        except Exception as e:
            logger.error(f"Failed to insert trade: {e}")
            raise

    def update_ohlc(self, product_id: str, time: str, price: float):
        try:
            exists = self.client.execute(
                """
                SELECT 1
                FROM coinbase_market_data.ohlc
                WHERE product_id = %(product_id)s AND time = toDateTime(%(time)s)
                """,
                {
                    'product_id': product_id,
                    'time': time
                }
            )
            
            if exists:
                self.client.execute(
                    """
                    ALTER TABLE coinbase_market_data.ohlc
                    UPDATE 
                        high = greatest(high, %(price)s),
                        low = least(low, %(price)s),
                        close = %(price)s
                    WHERE 
                        product_id = %(product_id)s AND
                        time = toDateTime(%(time)s)
                    """,
                    {
                        'product_id': product_id,
                        'time': time,
                        'price': price
                    }
                )
            else:
                self.client.execute(
                    """
                    INSERT INTO coinbase_market_data.ohlc
                    (product_id, time, open, high, low, close, volume)
                    VALUES (
                        %(product_id)s,
                        toDateTime(%(time)s),
                        %(price)s,
                        %(price)s,
                        %(price)s,
                        %(price)s,
                        0
                    )
                    """,
                    {
                        'product_id': product_id,
                        'time': time,
                        'price': price
                    }
                )
        except Exception as e:
            logger.error(f"Failed to update OHLC: {e}")
            raise

    def calculate_spreads(self, product_id: str):
        try:
            self.client.execute(
                """
                INSERT INTO coinbase_market_data.spreads
                (product_id, time, bid, ask, spread)
                SELECT 
                    product_id,
                    now() as time,
                    best_bid as bid,
                    best_ask as ask,
                    (best_ask - best_bid) as spread
                FROM coinbase_market_data.raw_trades
                WHERE product_id = %(product_id)s
                ORDER BY time DESC
                LIMIT 1
                """,
                {'product_id': product_id}
            )
        except Exception as e:
            logger.error(f"Failed to calculate spreads: {e}")
            raise