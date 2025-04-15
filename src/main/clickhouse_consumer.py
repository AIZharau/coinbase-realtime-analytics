import json
import signal
from typing import Dict, List
from confluent_kafka import Consumer, KafkaError
from utils.config import REDPANDA_CONFIG
from utils.logging import setup_logging
from utils.message_processor import MessageProcessor

logger = setup_logging(__name__)

class CoinbaseMarketDataConsumer:
    def __init__(self, config: Dict[str, str]):
        self.consumer = Consumer({
            'bootstrap.servers': config['bootstrap.servers'],
            'group.id': 'coinbase-consumer-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'debug': 'consumer'
        })
        self.processor = MessageProcessor()
        self.running = False

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def consume_messages(self, topics: List[str]):
        self.consumer.subscribe(topics)
        self.running = True
        logger.info(f"Subscribed to topics: {topics}")
        
        empty_polls = 0
        max_empty_polls = 10  
        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            
            if msg is None:
                empty_polls += 1
                if empty_polls >= max_empty_polls:
                    logger.warning(f"No messages received after {max_empty_polls} attempts")
                    break
                continue
            
            empty_polls = 0 

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info("Reached end of partition")
                    continue
                logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                message = json.loads(msg.value().decode('utf-8'))
                logger.info(f"Processing message: {message['product_id']} at {message['time']}") ##
                self.processor.process_message(message)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except KeyError as e:
                logger.error(f"Missing expected field in message: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

        logger.info("Finished consuming messages")

    def close(self):
        if hasattr(self, 'consumer'):
            self.consumer.close()

if __name__ == '__main__':
    consumer = CoinbaseMarketDataConsumer(REDPANDA_CONFIG)
    try:
        consumer.consume_messages(topics=['coinbase_market_data'])
    except Exception as e:
        logger.exception("Fatal error in consumer")
    finally:
        consumer.close()