import json
import websocket
import threading
import time
import os
import sys
import socket
from confluent_kafka import Producer
from utils.config import REDPANDA_CONFIG
from utils.logging import setup_logging
from utils.data_formatter import CoinbaseDataFormatter

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.connection_helper import wait_for_service

logger = setup_logging(__name__)

class CoinbaseWebSocketProducer:
    def __init__(self):
        logger.info("Initializing producer...")
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.products = ["BTC-USD", "ETH-USD"]
        self.channels = ["ticker"] # "heartbeats"
        self.ws = None
        self.topic = 'coinbase_market_data'
        
        redpanda_brokers = os.environ.get('REDPANDA_BROKERS', REDPANDA_CONFIG['bootstrap.servers'])
        
        self._wait_for_redpanda(redpanda_brokers)

        self.producer = Producer({
            'bootstrap.servers': REDPANDA_CONFIG['bootstrap.servers'],
            'queue.buffering.max.kbytes': 1024,
            'batch.num.messages': 500,
            'linger.ms': 50,
            'compression.type': 'zstd',
            'enable.idempotence': True,
            'max.in.flight.requests.per.connection': 1,
            'message.max.bytes': 10485760,
            'error_cb': self._error_callback
        })
    
    def _wait_for_redpanda(self, redpanda_brokers):
        try:
            redpanda_host = redpanda_brokers.split(':')[0]
            redpanda_port = int(redpanda_brokers.split(':')[1])
            
            logger.info(f"Waiting for Redpanda at {redpanda_host}:{redpanda_port}...")
            if not wait_for_service(redpanda_host, redpanda_port, timeout=300, interval=5):
                logger.error("Failed to connect to Redpanda, exiting")
                sys.exit(1)
                
            logger.info("Redpanda is available")
        except Exception as e:
            logger.error(f"Error waiting for Redpanda: {e}")
            sys.exit(1)

    def _error_callback(self, error):
        logger.error(f"Producer error: {error}")
        
    def prepare_data(self, data, ctx=None):
        return CoinbaseDataFormatter.prepare_producer_data(data)

    def validate_message(self, data):
        required_fields = [
            'type', 'sequence', 'product_id', 'price', 
            'time', 'trade_id'
        ]
        return all(field in data for field in required_fields)

    def _delivery_callback(self, err, msg):
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()}")

    def on_message(self, ws, message):
        data = json.loads(message)
        if data.get('type') in ['subscriptions', 'heartbeat']:
            return
        if not self.validate_message(data):
            return

        self.producer.produce(
            topic=self.topic, 
            value=json.dumps(self.prepare_data(data)).encode('utf-8'),
            key=data['product_id'].encode('utf-8'),
            callback=self._delivery_callback
        )
        logger.info(f"Produced message - Product: {data['product_id']}, Price: {data['price']}, Time: {data['time']}")
    

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("Connection closed")
        self.producer.flush()

    def on_open(self, ws):
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": self.products,
            "channels": self.channels
        }
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to {self.products}")

    def run(self):
        logger.info("Connecting to Coinbase WebSocket...")
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close 
        )
        
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Closing connection...")
            self.ws.close()
            self.producer.flush()

if __name__ == '__main__':
    logger.info("Starting application...")
    try:
        producer = CoinbaseWebSocketProducer()
        producer.run()
    except Exception as e:
        logger.exception("Fatal error occures")
        raise 