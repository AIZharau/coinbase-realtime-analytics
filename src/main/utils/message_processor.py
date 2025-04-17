from datetime import datetime
from typing import Dict
from .clickhouse_client import ClickHouseClient
from .config import CLICKHOUSE_CONFIG
from .data_formatter import CoinbaseDataFormatter
from .logging import setup_logging

logger = setup_logging(__name__)

class MessageProcessor:
    AGGREGATION_INTERVAL = 15  # seconds
    PRICE_JUMP_THRESHOLD = 0.05  # 5%
    VOLUME_SPIKE_THRESHOLD = 3  # 3x

    def __init__(self):
        self.ch_client = ClickHouseClient(CLICKHOUSE_CONFIG)
        self.last_prices = {}
        self.last_aggregation_time = None

    def process_message(self, message: Dict):
        """Main message processing pipeline"""
        try:
            self._store_raw_data(message)
            
            if self._should_aggregate():
                self._process_aggregates(message['product_id'])
                self.last_aggregation_time = datetime.now()
                
            self._detect_anomalies(message)
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            raise

    def _store_raw_data(self, message: Dict):
        """Store raw trade data in ClickHouse"""
        formatted_data = CoinbaseDataFormatter.prepare_clickhouse_data(message)
        self.ch_client.insert_raw_trade(formatted_data)

    def _should_aggregate(self) -> bool:
        """Check if we need to perform aggregation"""
        return (self.last_aggregation_time is None or 
                (datetime.now() - self.last_aggregation_time).total_seconds() >= self.AGGREGATION_INTERVAL)

    def _process_aggregates(self, product_id: str):
        aggregates = [
            {
                'name': 'ohlc',
                'query': """
                INSERT INTO coinbase_market_data.ohlc
                SELECT
                    product_id,
                    toStartOfMinute(time) AS time,
                    argMin(price, time) AS open,
                    max(price) AS high,
                    min(price) AS low,
                    argMax(price, time) AS close,
                    sum(last_size) AS volume
                FROM coinbase_market_data.raw_trades
                WHERE product_id = %(product_id)s
                GROUP BY product_id, toStartOfMinute(time), time
                """
            },
            {
                'name': 'spread',
                'query': """
                INSERT INTO coinbase_market_data.spreads
                SELECT
                    product_id,
                    now(),
                    best_ask - best_bid,
                    best_bid,
                    best_ask,
                    best_bid_size,
                    best_ask_size
                FROM coinbase_market_data.raw_trades
                WHERE product_id = %(product_id)s
                ORDER BY time DESC
                LIMIT 1
                """
            }
        ]

        params = {'product_id': product_id}
        
        for agg in aggregates:
            try:
                self.ch_client.client.execute(agg['query'], params)
                logger.info(f"{agg['name'].upper()} aggregation completed")
            except Exception as e:
                logger.error(f"{agg['name'].upper()} aggregation failed: {str(e)}")
                raise

    def _detect_anomalies(self, message: Dict):
        product_id = message['product_id']
        current_price = float(message['price'])
        current_volume = float(message.get('last_size', 0))
        
        if product_id not in self.last_prices:
            self._init_price_record(product_id, current_price, current_volume, message['time'])
            return

        last = self.last_prices[product_id]
        price_jump, volume_spike = self._calculate_metrics(current_price, current_volume, last)

        if self._is_anomaly(price_jump, volume_spike):
            self._log_anomaly(
                product_id=product_id,
                time=message['time'],
                metrics=(price_jump, volume_spike),
                prices=(current_price, last['price']),
                volumes=(current_volume, last['volume'])
            )

        self._update_price_record(product_id, current_price, current_volume, message['time'])

    def _init_price_record(self, product_id: str, price: float, volume: float, time: str):
        self.last_prices[product_id] = {
            'price': price,
            'volume': volume,
            'time': time
        }

    def _calculate_metrics(self, current_price: float, current_volume: float, last: Dict) -> tuple:
        price_jump = abs(current_price - last['price']) / last['price']
        volume_spike = current_volume / last['volume'] if last['volume'] > 0 else 0
        return price_jump, volume_spike

    def _is_anomaly(self, price_jump: float, volume_spike: float) -> bool:
        return (price_jump > self.PRICE_JUMP_THRESHOLD or 
                volume_spike > self.VOLUME_SPIKE_THRESHOLD)

    def _log_anomaly(self, product_id: str, time: str, metrics: tuple, prices: tuple, volumes: tuple):
        price_jump, volume_spike = metrics
        current_price, last_price = prices
        current_volume, last_volume = volumes

        details = (f"Price jump: {price_jump:.2%}, Volume spike: {volume_spike:.2%}, "
                   f"Current: {current_price}/{current_volume}, Last: {last_price}/{last_volume}")

        try:
            self.ch_client.client.execute(
                """
                INSERT INTO coinbase_market_data.anomalies
                (product_id, time, price_jump, volume_spike, 
                 current_price, last_price, current_volume, last_volume, details)
                VALUES (%(product_id)s, toDateTime(%(time)s), %(price_jump)s, 
                        %(volume_spike)s, %(current_price)s, %(last_price)s,
                        %(current_volume)s, %(last_volume)s, %(details)s)
                """,
                {
                    'product_id': product_id,
                    'time': time,
                    'price_jump': price_jump,
                    'volume_spike': volume_spike,
                    'current_price': current_price,
                    'last_price': last_price,
                    'current_volume': current_volume,
                    'last_volume': last_volume,
                    'details': details
                }
            )
            logger.warning(f"Anomaly detected: {product_id} - {details}")
        except Exception as e:
            logger.error(f"Failed to log anomaly: {str(e)}")
            raise

    def _update_price_record(self, product_id: str, price: float, volume: float, time: str):
        self.last_prices[product_id] = {
            'price': price,
            'volume': volume,
            'time': time
        }