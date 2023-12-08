from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
import pymongo
from datetime import datetime
import os 
from dotenv import load_dotenv
# Đường dẫn tuyệt đối đến file .env
dotenv_path = '//Volumes/Project/Tas_QA/Mongo Data/.env'
load_dotenv(dotenv_path=dotenv_path)
api_key = os.environ.get("CENTIC_API_KEY")
client_url = os.environ.get("MONGO_URL")
default_args = {
    'owner': 'user',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 8),
    'retries': 1,
}
def crawl_coingecko_data():
    for page in range(1, 46):
        url = 'https://pro-api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': '250',
            'page': str(page),
            'sparkline': 'false',
            'price_change_percentage': '24h,7d,14d,30d',
            'x_cg_pro_api_key': api_key
        }
        
        response = requests.get(url, params=params)

        if response.status_code == 200:
            coin_data = response.json()
            for item in coin_data:
                if 'fully_diluted_valuation' in item and item['fully_diluted_valuation'] is not None:
                    item['fully_diluted_valuation'] /= 1000000000  # fix len
                    
            collection.insert_many(coin_data)
            print(f"Page {page} have crawled sucessfull.")
        else:
            print(f"Failed to crawled data for page {page}. Status code: {response.status_code}")

    collection.update_many({}, [{"$set": {"symbol": {"$toUpper": "$symbol"}}}])
    print("All data saved to MongoDB")
def update_data_to_mongodb():
    client = pymongo.MongoClient(client_url)
    db = client["LLM_DataLake"]
    collection = db['Coingecko_allcoin']
    collection.update_many({}, [{"$set": {"symbol": {"$toUpper": "$symbol"}}}])
    print("All data saved to MongoDB")

dag = DAG('All_coingecko_info', default_args=default_args, schedule_interval='@daily')

crawl_task = PythonOperator(
    task_id='crawl_coingecko_data',
    python_callable=crawl_coingecko_data,
    dag=dag,
)

update_task = PythonOperator(
    task_id='update_data_to_mongodb',
    python_callable=update_data_to_mongodb,
    dag=dag,
)

crawl_task >> update_task

