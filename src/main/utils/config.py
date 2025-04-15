import os

REDPANDA_CONFIG = {
    'bootstrap.servers': os.getenv('REDPANDA_BROKERS', 'localhost:19092'),
    'group.id': 'coinbase-market-data-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', '9000')),
    'database': 'coinbase_market_data',
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password'),
    'connect_timeout': 10
}