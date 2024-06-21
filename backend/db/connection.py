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

# def insert_article_to_db(articles):
#     connection = connect_to_db()
#     cursor = connection.cursor()
#
#     for article in articles:
#         cursor.execute("""
#                INSERT INTO lng.logistics_news_articles (news_datetime, fetch_datetime, news_text, website_url, title)
#                VALUES (?, ?, ?, ?, ?)
#            """,
#                        article['news_datetime'],
#                        article['fetch_datetime'],
#                        article['news_text'],
#                        article['website_url'],
#                        article['title'])
#
#     connection.commit()
#     cursor.close()
#     connection.close()
#

def insert_article_to_db(articles):
    connection = connect_to_db()
    cursor = connection.cursor()

    for article in articles:
        cursor.execute("""
               INSERT INTO lng.test_logistics_news_articles (news_datetime, fetch_datetime, news_text, website_url, title)
               VALUES (?, ?, ?, ?, ?)
           """,
                       article['news_datetime'],
                       article['fetch_datetime'],
                       article['news_text'],
                       article['website_url'],
                       article['title'])

    connection.commit()
    cursor.close()
    connection.close()

def insert_user_keyphrases(email):
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("""
        MERGE INTO lng.users AS target
        USING (SELECT ? AS email) AS source
        ON (target.email = source.email)
        WHEN MATCHED THEN
            UPDATE SET email = source.email
        WHEN NOT MATCHED THEN
            INSERT (email) VALUES (source.email);
    """, email)

    connection.commit()
    cursor.close()
    connection.close()

def remove_duplicate_articles():
    connection = connect_to_db()
    cursor = connection.cursor()

    # Remove duplicates based on website_url, keeping the first occurrence
    delete_duplicates_query = """
    WITH CTE AS (
        SELECT 
            id,
            website_url,
            ROW_NUMBER() OVER (PARTITION BY website_url ORDER BY id) AS rn
        FROM [lng].[test_logistics_news_articles]
    )
    DELETE FROM CTE WHERE rn > 1;
    """

    cursor.execute(delete_duplicates_query)
    connection.commit()

    cursor.close()
    connection.close()