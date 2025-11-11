"""
KiotViet ETL DAG - Orchestrate token fetch, product export, invoice sync, and upload to Blob
"""

from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.decorators import apply_defaults
from airflow.models import Variable

# Add project path
PROJECT_DIR = Path('/home/hhaiviet/kiotviet-integration')
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.services.product_service import ProductService
from src.services.invoice_service import InvoiceService
from src.services.token_service import TokenService
from src.models.credentials import AccessCredentials
from src.utils.azure_blob import upload_to_azure_blob
from src.utils.logger import logger


# Default DAG arguments
default_args = {
    'owner': 'kiotviet-integration',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 9),
    'email': ['hhaiviet@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'kiotviet_etl',
    default_args=default_args,
    description='KiotViet ETL: Token Fetch -> Product Export -> Invoice Sync -> Upload to Blob',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['kiotviet', 'etl', 'production'],
)


def fetch_token_task(**context):
    """Task 1: Fetch fresh JWT token from KiotViet API"""
    logger.info("🔓 TASK 1: Fetching token from KiotViet API...")
    
    try:
        import requests
        
        username = os.getenv('KIOTVIET_USERNAME', '0913431718')
        password = os.getenv('KIOTVIET_PASSWORD', '68686868')
        
        url = 'https://api-man1.kiotviet.vn/api/account/login?quan-ly=true'
        headers = {
            'Retailer': '248minimart',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': {
                'UserName': username,
                'Password': password,
                'RememberMe': False,
                'ShowCaptcha': False,
                'Language': 'vi-VN',
                'LatestBranchId': 291407,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('result'):
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
        
        token = data['result'].get('access_token')
        if not token:
            raise Exception("No token in response")
        
        # Save token to file
        token_file = PROJECT_DIR / 'data' / 'credentials' / 'token.json'
        token_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        token_data = {
            'access_token': token,
            'retailer_id': '248minimart',
            'branch_id': 291407,
        }
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        logger.info("✅ Token fetched and saved successfully")
        context['task_instance'].xcom_push(key='token', value=token)
        return {'status': 'success', 'token': token}
        
    except Exception as e:
        logger.error(f"❌ Token fetch failed: {e}")
        raise


def export_products_task(**context):
    """Task 2: Export products from KiotViet API"""
    logger.info("📦 TASK 2: Exporting products...")
    
    try:
        service = ProductService()
        result = service.export()
        
        logger.info(f"✅ Product export completed: {result.products} items in {result.duration_seconds:.1f}s")
        context['task_instance'].xcom_push(key='product_count', value=result.products)
        context['task_instance'].xcom_push(key='product_file', value=str(result.output_file))
        
        return {'status': 'success', 'products': result.products, 'file': str(result.output_file)}
        
    except Exception as e:
        logger.error(f"❌ Product export failed: {e}")
        raise


def upload_products_task(**context):
    """Task 3: Upload product CSV to Blob Storage"""
    logger.info("☁️ TASK 3: Uploading products to Blob Storage...")
    
    try:
        product_file = context['task_instance'].xcom_pull(key='product_file', task_ids='export_products')
        
        if not product_file:
            raise Exception("Product file path not found in XCom")
        
        blob_url = upload_to_azure_blob(product_file, 'master_products.csv')
        logger.info(f"✅ Product data uploaded to Blob: {blob_url}")
        
        return {'status': 'success', 'blob_url': blob_url}
        
    except Exception as e:
        logger.error(f"❌ Product upload failed: {e}")
        raise


def export_invoices_task(**context):
    """Task 4: Sync invoices from KiotViet API"""
    logger.info("📋 TASK 4: Syncing invoices...")
    
    try:
        service = InvoiceService()
        result = service.sync(incremental=True)
        
        logger.info(f"✅ Invoice sync completed: {result.invoices} invoices, {result.lines} lines in {result.duration_seconds:.1f}s")
        context['task_instance'].xcom_push(key='invoice_count', value=result.invoices)
        context['task_instance'].xcom_push(key='invoice_lines', value=result.lines)
        context['task_instance'].xcom_push(key='invoice_file', value=str(result.output_file))
        
        return {
            'status': 'success',
            'invoices': result.invoices,
            'lines': result.lines,
            'file': str(result.output_file),
        }
        
    except Exception as e:
        logger.error(f"❌ Invoice sync failed: {e}")
        raise


def upload_invoices_task(**context):
    """Task 5: Upload invoice CSV to Blob Storage"""
    logger.info("☁️ TASK 5: Uploading invoices to Blob Storage...")
    
    try:
        invoice_file = context['task_instance'].xcom_pull(key='invoice_file', task_ids='export_invoices')
        
        if not invoice_file:
            raise Exception("Invoice file path not found in XCom")
        
        blob_url = upload_to_azure_blob(invoice_file, 'invoice_details.csv')
        logger.info(f"✅ Invoice data uploaded to Blob: {blob_url}")
        
        return {'status': 'success', 'blob_url': blob_url}
        
    except Exception as e:
        logger.error(f"❌ Invoice upload failed: {e}")
        raise


def summary_task(**context):
    """Task 6: Print summary of all operations"""
    logger.info("📊 TASK 6: Summary...")
    
    try:
        product_count = context['task_instance'].xcom_pull(key='product_count', task_ids='export_products')
        invoice_count = context['task_instance'].xcom_pull(key='invoice_count', task_ids='export_invoices')
        invoice_lines = context['task_instance'].xcom_pull(key='invoice_lines', task_ids='export_invoices')
        
        summary = f"""
        
        ✅ ETL Pipeline Completed Successfully!
        
        📊 Summary:
        - Products: {product_count} items
        - Invoices: {invoice_count} invoices, {invoice_lines} lines
        - All files uploaded to Azure Blob Storage
        
        Timestamp: {datetime.now().isoformat()}
        """
        
        logger.info(summary)
        return {'status': 'success', 'summary': summary}
        
    except Exception as e:
        logger.error(f"❌ Summary failed: {e}")
        raise


# Define tasks
t1_fetch_token = PythonOperator(
    task_id='fetch_token',
    python_callable=fetch_token_task,
    dag=dag,
)

t2_export_products = PythonOperator(
    task_id='export_products',
    python_callable=export_products_task,
    dag=dag,
)

t3_upload_products = PythonOperator(
    task_id='upload_products',
    python_callable=upload_products_task,
    dag=dag,
)

t4_export_invoices = PythonOperator(
    task_id='export_invoices',
    python_callable=export_invoices_task,
    dag=dag,
)

t5_upload_invoices = PythonOperator(
    task_id='upload_invoices',
    python_callable=upload_invoices_task,
    dag=dag,
)

t6_summary = PythonOperator(
    task_id='summary',
    python_callable=summary_task,
    dag=dag,
)

# Define dependencies
t1_fetch_token >> [t2_export_products, t4_export_invoices]
t2_export_products >> t3_upload_products
t4_export_invoices >> t5_upload_invoices
[t3_upload_products, t5_upload_invoices] >> t6_summary
