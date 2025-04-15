from typing import Dict
from datetime import datetime
from .logging import setup_logging

logger = setup_logging(__name__)

class CoinbaseDataFormatter:
    @staticmethod
    def prepare_producer_data(raw_data: Dict) -> Dict:
        return {
            'type': raw_data['type'],
            'sequence': int(raw_data['sequence']),
            'product_id': raw_data['product_id'],
            'price': float(raw_data['price']),
            'open_24h': float(raw_data['open_24h']),
            'volume_24h': float(raw_data['volume_24h']),
            'low_24h': float(raw_data['low_24h']),
            'high_24h': float(raw_data['high_24h']),
            'volume_30d': float(raw_data['volume_30d']),
            'best_bid': float(raw_data['best_bid']),
            'best_bid_size': float(raw_data['best_bid_size']),
            'best_ask': float(raw_data['best_ask']),
            'best_ask_size': float(raw_data['best_ask_size']),
            'side': raw_data.get('side'),
            'time': raw_data['time'],
            'trade_id': int(raw_data['trade_id']),
            'last_size': float(raw_data['last_size'])
        }

    @staticmethod
    def prepare_clickhouse_data(raw_data: Dict) -> Dict:
        try: 
            dt = datetime.strptime(raw_data['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        except Exception as e:
            print(f"ERROR: Time parsing failed: {e}")
            formatted_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        return {
            'type': raw_data.get('type'),
            'sequence': int(raw_data.get('sequence', 0)),
            'product_id': raw_data.get('product_id'),
            'price': float(raw_data.get('price', 0)),
            'open_24h': float(raw_data.get('open_24h', 0)),
            'volume_24h': float(raw_data.get('volume_24h', 0)),
            'low_24h': float(raw_data.get('low_24h', 0)),
            'high_24h': float(raw_data.get('high_24h', 0)),
            'volume_30d': float(raw_data.get('volume_30d', 0)),
            'best_bid': float(raw_data.get('best_bid', 0)),
            'best_bid_size': float(raw_data.get('best_bid_size', 0)),
            'best_ask': float(raw_data.get('best_ask', 0)),
            'best_ask_size': float(raw_data.get('best_ask_size', 0)),
            'side': raw_data.get('side'),
            'time': formatted_time,
            'trade_id': int(raw_data.get('trade_id', 0)),
            'last_size': float(raw_data.get('last_size', 0))
        }