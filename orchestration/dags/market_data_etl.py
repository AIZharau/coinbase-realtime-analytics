"""
Coinbase Market Data ETL Process

This DAG handles the ETL process for Coinbase Market Data:
1. Checks if the data is available
2. Aggregates the trade data
3. Calculates analytics metrics
4. Generates reports
"""

from datetime import datetime, timedelta
import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.models import Variable
from airflow.hooks.base import BaseHook

default_args = {
    'owner': 'data_engineers',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': pendulum.datetime(2023, 1, 1, tz="UTC"),
}

def check_clickhouse_data(**kwargs):
    from clickhouse_driver import Client
    
    conn = BaseHook.get_connection('clickhouse_default')
    client = Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )
    
    execution_date = kwargs['execution_date']
    date_str = execution_date.strftime('%Y-%m-%d')
    
    result = client.execute(
        f"""
        SELECT count() 
        FROM coinbase_market_data.raw_trades 
        WHERE toDate(time) = '{date_str}'
        """
    )
    
    count = result[0][0]
    print(f"Found {count} records for {date_str}")
    
    return count > 0

def aggregate_hourly_data(**kwargs):
    from clickhouse_driver import Client
    
    conn = BaseHook.get_connection('clickhouse_default')
    client = Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )
    
    execution_date = kwargs['execution_date']
    date_str = execution_date.strftime('%Y-%m-%d')
    
    client.execute(
        f"""
        INSERT INTO coinbase_market_data.hourly_stats
        SELECT 
            product_id,
            toStartOfHour(time) AS hour,
            avg(price) AS avg_price,
            min(price) AS min_price,
            max(price) AS max_price,
            sum(last_size) AS volume
        FROM coinbase_market_data.raw_trades
        WHERE toDate(time) = '{date_str}'
        GROUP BY product_id, hour
        """
    )
    
    return True

def analyze_price_volatility(**kwargs):
    from clickhouse_driver import Client
    import pandas as pd
    import numpy as np
    
    conn = BaseHook.get_connection('clickhouse_default')
    client = Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )
    
    execution_date = kwargs['execution_date']
    date_str = execution_date.strftime('%Y-%m-%d')
    
    result = client.execute(
        f"""
        SELECT 
            product_id,
            hour,
            avg_price,
            max_price - min_price AS price_range,
            max_price / nullIf(min_price, 0) AS price_ratio,
            volume
        FROM coinbase_market_data.hourly_stats
        WHERE toDate(hour) = '{date_str}'
        ORDER BY product_id, hour
        """,
        with_column_types=True
    )
    
    rows, columns = result
    column_names = [col[0] for col in columns]
    df = pd.DataFrame(rows, columns=column_names)
    
    volatility_results = []
    for product in df['product_id'].unique():
        product_df = df[df['product_id'] == product]
        if len(product_df) > 1:
            price_std = np.std(product_df['avg_price'])
            price_mean = np.mean(product_df['avg_price'])
            coefficient_of_variation = (price_std / price_mean) * 100 if price_mean > 0 else 0
            
            volatility_results.append({
                'product_id': product,
                'date': date_str,
                'price_std': float(price_std),
                'price_mean': float(price_mean),
                'coefficient_of_variation': float(coefficient_of_variation)
            })
    
    for result in volatility_results:
        client.execute(
            """
            INSERT INTO coinbase_market_data.volatility_metrics
            (product_id, date, price_std, price_mean, coefficient_of_variation)
            VALUES
            """,
            [
                (
                    result['product_id'],
                    result['date'],
                    result['price_std'],
                    result['price_mean'],
                    result['coefficient_of_variation']
                )
            ]
        )
    
    return True

with DAG(
    'coinbase_market_data_etl',
    default_args=default_args,
    description='ETL process for Coinbase market data',
    schedule='@daily',
    catchup=False,
    tags=['crypto', 'etl', 'coinbase'],
) as dag:
    
    check_data = PythonOperator(
        task_id='check_data_availability',
        python_callable=check_clickhouse_data,
        provide_context=True,
    )
    
    aggregate_data = PythonOperator(
        task_id='aggregate_hourly_data',
        python_callable=aggregate_hourly_data,
        provide_context=True,
    )
    
    analyze_volatility = PythonOperator(
        task_id='analyze_price_volatility',
        python_callable=analyze_price_volatility,
        provide_context=True,
    )
    
    check_data >> aggregate_data >> analyze_volatility 