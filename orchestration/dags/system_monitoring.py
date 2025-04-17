"""
System Monitoring DAG

This DAG monitors the health and performance of the Coinbase Analytics platform:
1. Check service availability
2. Monitor database metrics
3. Check data pipeline health
4. Report system health
"""

from datetime import datetime, timedelta
import pendulum
import os
import json
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from airflow.providers.http.sensors.http import HttpSensor

default_args = {
    'owner': 'system_engineers',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': pendulum.datetime(2023, 1, 1, tz="UTC"),
}

def check_clickhouse_health(**kwargs):
    from clickhouse_driver import Client
    from airflow.hooks.base import BaseHook
    import time
    
    conn = BaseHook.get_connection('clickhouse_default')
    client = Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )
    
    start_time = time.time()
    result = client.execute("SELECT 1")
    response_time = time.time() - start_time
    
    metrics = {
        'response_time': response_time,
        'is_available': result[0][0] == 1,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        disk_usage = client.execute("SELECT formatReadableSize(sum(bytes)) FROM system.parts")
        metrics['disk_usage'] = disk_usage[0][0] if disk_usage else "Unknown"
        
        table_count = client.execute("SELECT count() FROM system.tables WHERE database = %s", (conn.schema,))
        metrics['table_count'] = table_count[0][0] if table_count else 0
        
        row_count = client.execute("""
            SELECT 
                sum(rows) 
            FROM system.parts 
            WHERE database = %s AND active
        """, (conn.schema,))
        metrics['row_count'] = row_count[0][0] if row_count else 0
    except Exception as e:
        print(f"Error getting ClickHouse metrics: {e}")
        metrics['error'] = str(e)
    
    print(f"ClickHouse Metrics: {json.dumps(metrics, indent=2)}")
    return metrics

def check_redpanda_health(**kwargs):
    import subprocess
    
    metrics = {
        'is_available': False,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        result = subprocess.run(
            ["rpk", "cluster", "health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "HEALTHY" in result.stdout:
            metrics['is_available'] = True
            metrics['status'] = "HEALTHY"
        else:
            metrics['status'] = "UNHEALTHY"
            metrics['error'] = result.stdout
        
        topics_result = subprocess.run(
            ["rpk", "topic", "list", "-j"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        topics_data = json.loads(topics_result.stdout)
        metrics['topic_count'] = len(topics_data)
        metrics['topics'] = [t.get('name') for t in topics_data]
        
    except Exception as e:
        print(f"Error checking Redpanda health: {e}")
        metrics['error'] = str(e)
    
    print(f"Redpanda Metrics: {json.dumps(metrics, indent=2)}")
    return metrics

def check_pipeline_status(**kwargs):
    from clickhouse_driver import Client
    from airflow.hooks.base import BaseHook
    
    conn = BaseHook.get_connection('clickhouse_default')
    client = Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )
    
    try:
        result = client.execute("""
            SELECT 
                max(time) as latest_time,
                now() as current_time,
                dateDiff('minute', max(time), now()) as lag_minutes
            FROM coinbase_market_data.raw_trades
        """)
        
        latest_time, current_time, lag_minutes = result[0]
        
        pipeline_status = {
            'latest_data_time': latest_time.isoformat() if latest_time else None,
            'current_time': current_time.isoformat() if current_time else None,
            'lag_minutes': lag_minutes,
            'is_healthy': lag_minutes < 15,  # Consider healthy if less than 15 minutes behind
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error checking pipeline status: {e}")
        pipeline_status = {
            'error': str(e),
            'is_healthy': False,
            'timestamp': datetime.now().isoformat()
        }
    
    print(f"Pipeline Status: {json.dumps(pipeline_status, indent=2)}")
    return pipeline_status

def generate_health_report(**kwargs):
    ti = kwargs['ti']
    
    clickhouse_metrics = ti.xcom_pull(task_ids='check_clickhouse_health')
    redpanda_metrics = ti.xcom_pull(task_ids='check_redpanda_health')
    pipeline_status = ti.xcom_pull(task_ids='check_pipeline_status')
    
    is_healthy = (
        clickhouse_metrics.get('is_available', False) and
        redpanda_metrics.get('is_available', False) and
        pipeline_status.get('is_healthy', False)
    )
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_health': 'HEALTHY' if is_healthy else 'UNHEALTHY',
        'components': {
            'clickhouse': clickhouse_metrics,
            'redpanda': redpanda_metrics,
            'data_pipeline': pipeline_status
        }
    }
    
    report_path = f"/opt/airflow/logs/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Health report generated and saved to {report_path}")
    print(f"Overall System Health: {report['overall_health']}")
    
    return report

with DAG(
    'system_monitoring',
    default_args=default_args,
    description='Monitor system health and performance',
    schedule='@hourly',
    catchup=False,
    tags=['monitoring', 'health', 'system'],
) as dag:
    
    check_clickhouse = PythonOperator(
        task_id='check_clickhouse_health',
        python_callable=check_clickhouse_health,
        provide_context=True,
    )
    
    check_redpanda = PythonOperator(
        task_id='check_redpanda_health',
        python_callable=check_redpanda_health,
        provide_context=True,
    )
    
    check_pipeline = PythonOperator(
        task_id='check_pipeline_status',
        python_callable=check_pipeline_status,
        provide_context=True,
    )
    
    generate_report = PythonOperator(
        task_id='generate_health_report',
        python_callable=generate_health_report,
        provide_context=True,
    )
    
    [check_clickhouse, check_redpanda, check_pipeline] >> generate_report 