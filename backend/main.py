import os
import pyodbc
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import numpy as np
import torch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database credentials from environment variables
server = 'tcp:tep-db-test.database.windows.net,1433'
database = 'logistics-news-aggregator-db'
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
driver = 'ODBC Driver 18 for SQL Server'

# Connect to the database
def connect_to_db():
    print('Connecting to the database...')
    conn_str = f'Driver={{{driver}}};Server={server};Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    connection = pyodbc.connect(conn_str)
    print('connected')
    return connection

# Fetch articles from the database
def fetch_articles(connection):
    query = "SELECT * FROM Articles"
    articles_df = pd.read_sql(query, connection)
    return articles_df

# Fetch user preferences from the database
def fetch_user_preferences(connection):
    query = "SELECT * FROM UserPreferences"
    preferences_df = pd.read_sql(query, connection)
    return preferences_df

# Calculate TF-IDF and Cosine Similarity
def calculate_tfidf_cosine_similarity(user_keywords, article_content):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([user_keywords, article_content])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return cosine_sim[0][0]

# Calculate Semantic Similarity
def calculate_semantic_similarity(user_paragraph, article_content):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    
    def get_embedding(text):
        inputs = tokenizer(text, return_tensors='pt', max_length=512, truncation=True, padding=True)
        outputs = model(**inputs)
        return np.mean(outputs.last_hidden_state.detach().numpy(), axis=1).flatten()
    
    user_embedding = get_embedding(user_paragraph)
    article_embedding = get_embedding(article_content)
    
    cosine_sim = np.dot(user_embedding, article_embedding) / (np.linalg.norm(user_embedding) * np.linalg.norm(article_embedding))
    return cosine_sim

# Combine and normalize scores
def calculate_relevance_score(user_keywords, user_paragraph, article_content):
    tfidf_cosine_sim = calculate_tfidf_cosine_similarity(user_keywords, article_content)
    semantic_similarity = calculate_semantic_similarity(user_paragraph, article_content)
    
    # Combine scores (adjust weights as needed)
    combined_score = 0.5 * tfidf_cosine_sim + 0.5 * semantic_similarity
    
    # Normalize score
    normalized_score = min(max(combined_score, 0), 1)
    return normalized_score

def main():
    print('hammad')
    connection = connect_to_db()
    print(connection)
    
    # articles = fetch_articles(connection)
    # preferences = fetch_user_preferences(connection)
    
    # for _, pref_row in preferences.iterrows():
    #     user_id = pref_row['user_id']
    #     user_keywords = pref_row['keywords']
    #     user_paragraph = pref_row['paragraph']
        
    #     for _, article_row in articles.iterrows():
    #         article_content = article_row['content']
    #         relevance_score = calculate_relevance_score(user_keywords, user_paragraph, article_content)
            
    #         print(f"User {user_id}, Article {article_row['article_id']}, Relevance Score: {relevance_score}")

if __name__ == "__main__":
    main()
