CREATE database coinbase_market_data;

CREATE TABLE coinbase_market_data.raw_trades_stream (
    type String,
    sequence Int64,
    product_id String,
    price Float64,
    open_24h Float64,
    volume_24h Float64,
    low_24h Float64,
    high_24h Float64,
    volume_30d Float64,
    best_bid Float64,
    best_bid_size Float64,
    best_ask Float64,
    best_ask_size Float64,
    side Nullable(String),
    time DateTime64(3),
    trade_id Int64,
    last_size Float64
) ENGINE = Kafka() 
SETTINGS 
kafka_broker_list = 'redpanda:9092',
kafka_topic_list = 'coinbase_market_data',
kafka_group_name = 'coinbase-market-data-group',
kafka_format = 'JSONEachRow';


CREATE TABLE coinbase_market_data.raw_trades (
    type String,
    sequence Int64,
    product_id String,
    price Float64,
    open_24h Float64,
    volume_24h Float64,
    low_24h Float64,
    high_24h Float64,
    volume_30d Float64,
    best_bid Float64,
    best_bid_size Float64,
    best_ask Float64,
    best_ask_size Float64,
    side Nullable(String),
    time DateTime64(3),
    trade_id Int64,
    last_size Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);


CREATE MATERIALIZED VIEW coinbase_market_data.trades_in_mv TO coinbase_market_data.raw_trades
AS
SELECT *
FROM coinbase_market_data.raw_trades_stream
SETTINGS
materialized_views_ignore_errors = false;

CREATE TABLE IF NOT EXISTS coinbase_market_data.ohlc (
    product_id String,
    time DateTime,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);

CREATE TABLE IF NOT EXISTS coinbase_market_data.spreads (
    product_id String,
    time DateTime,
    spread Float64,
    bid Float64,
    ask Float64,
    bid_size Float64,
    ask_size Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);

CREATE TABLE IF NOT EXISTS coinbase_market_data.anomalies (
    product_id String,
    time DateTime,
    price_jump Float64,
    volume_spike Float64,
    current_price Float64,
    last_price Float64,
    current_volume Float64,
    last_volume Float64,
    details String
) ENGINE = MergeTree()
ORDER BY (product_id, time);