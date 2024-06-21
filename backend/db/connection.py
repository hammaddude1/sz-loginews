import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database credentials from environment variables
server = 'tcp:tep-db-test.database.windows.net,1433'
database = 'logistics-news-aggregator-db'
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
driver = 'ODBC Driver 18 for SQL Server'

def connect_to_db():
    conn_str = f'Driver={{{driver}}};Server={server};Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    connection = pyodbc.connect(conn_str)
    return connection

def fetch_articles(connection):
    query = "SELECT * FROM Articles"
    articles_df = pd.read_sql(query, connection)
    return articles_df

def fetch_user_preferences(connection):
    query = "SELECT * FROM UserPreferences"
    preferences_df = pd.read_sql(query, connection)
    return preferences_df
