"""
Infrastructure Management DAG

This DAG manages the infrastructure for the Coinbase Analytics platform using Terraform:
1. Check infrastructure state
2. Plan infrastructure changes
3. Apply infrastructure updates (with approval)
4. Validate infrastructure
"""

from datetime import datetime, timedelta
import pendulum
import os
import json
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable, TaskInstance
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.ssh.hooks.ssh import SSHHook

default_args = {
    'owner': 'platform_engineers',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': pendulum.datetime(2023, 1, 1, tz="UTC"),
}

TERRAFORM_PATH = '/opt/terraform'

def check_terraform_state(**kwargs):
    """Check if Terraform state exists and is valid"""
    ti = kwargs['ti']
    terraform_path = kwargs.get('terraform_path', TERRAFORM_PATH)
    
    bash_command = f"cd {terraform_path} && terraform show -json"
    
    stream = os.popen(bash_command)
    output = stream.read()
    
    try:
        tf_state = json.loads(output)
        resources = tf_state.get('values', {}).get('root_module', {}).get('resources', [])
        resource_count = len(resources)
        
        ti.xcom_push(key='terraform_resource_count', value=resource_count)
        ti.xcom_push(key='terraform_state_valid', value=True)
        
        print(f"Terraform state is valid with {resource_count} resources")
        return True
    except json.JSONDecodeError:
        print("Terraform state is invalid or missing")
        ti.xcom_push(key='terraform_state_valid', value=False)
        return False

def run_terraform_plan(**kwargs):
    ti = kwargs['ti']
    terraform_path = kwargs.get('terraform_path', TERRAFORM_PATH)
    
    bash_command = f"cd {terraform_path} && terraform plan -out=tfplan.binary && terraform show -json tfplan.binary"
    
    stream = os.popen(bash_command)
    output = stream.read()
    
    try:
        tf_plan = json.loads(output)
        has_changes = False
        
        if 'resource_changes' in tf_plan:
            for change in tf_plan['resource_changes']:
                if change.get('change', {}).get('actions') != ['no-op']:
                    has_changes = True
                    break
        
        ti.xcom_push(key='terraform_has_changes', value=has_changes)
        
        if has_changes:
            print("Terraform plan shows changes that need to be applied")
            return 'terraform_apply'
        else:
            print("Terraform plan shows no changes needed")
            return 'terraform_no_changes'
    except json.JSONDecodeError:
        print("Error parsing Terraform plan output")
        return 'terraform_error'

def check_terraform_success(**kwargs):
    ti = kwargs['ti']
    terraform_success = ti.xcom_pull(task_ids='terraform_apply', key='return_code') == 0
    
    if terraform_success:
        print("Terraform apply completed successfully")
        return 'terraform_validate'
    else:
        print("Terraform apply failed")
        return 'terraform_error'

with DAG(
    'infrastructure_management',
    default_args=default_args,
    description='Manage infrastructure with Terraform',
    schedule='@weekly',
    catchup=False,
    tags=['infrastructure', 'terraform', 'platform'],
) as dag:
    
    terraform_init = BashOperator(
        task_id='terraform_init',
        bash_command=f'cd {TERRAFORM_PATH} && terraform init',
    )
    
    check_state = PythonOperator(
        task_id='check_terraform_state',
        python_callable=check_terraform_state,
        provide_context=True,
    )
    
    terraform_plan = BranchPythonOperator(
        task_id='terraform_plan',
        python_callable=run_terraform_plan,
        provide_context=True,
    )
    
    terraform_apply = BashOperator(
        task_id='terraform_apply',
        bash_command=f'cd {TERRAFORM_PATH} && terraform apply -auto-approve tfplan.binary',
    )
    
    terraform_no_changes = EmptyOperator(
        task_id='terraform_no_changes',
    )
    
    check_apply = BranchPythonOperator(
        task_id='check_terraform_apply',
        python_callable=check_terraform_success,
        provide_context=True,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )
    
    terraform_validate = BashOperator(
        task_id='terraform_validate',
        bash_command=f'cd {TERRAFORM_PATH} && terraform validate',
    )
    
    terraform_error = EmptyOperator(
        task_id='terraform_error',
    )
    
    terraform_done = EmptyOperator(
        task_id='terraform_done',
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )
    
    terraform_init >> check_state >> terraform_plan
    terraform_plan >> [terraform_apply, terraform_no_changes]
    terraform_apply >> check_apply
    check_apply >> [terraform_validate, terraform_error]
    terraform_no_changes >> terraform_done
    terraform_validate >> terraform_done
    terraform_error >> terraform_done 