import time
from flask import Flask, jsonify
from db.connection import connect_to_db, fetch_articles, fetch_user_preferences
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import numpy as np
import torch

# Initialize Flask app
app = Flask(__name__)

def calculate_tfidf_cosine_similarity(user_keywords, article_content):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([user_keywords, article_content])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return cosine_sim[0][0]

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

def calculate_relevance_score(user_keywords, user_paragraph, article_content):
    tfidf_cosine_sim = calculate_tfidf_cosine_similarity(user_keywords, article_content)
    semantic_similarity = calculate_semantic_similarity(user_paragraph, article_content)
    
    combined_score = 0.5 * tfidf_cosine_sim + 0.5 * semantic_similarity
    normalized_score = min(max(combined_score, 0), 1)
    return normalized_score

@app.route('/process', methods=['GET'])
def process():
    connection = connect_to_db()
    print('yolsadsao')
    return "2321312"
    
    # articles = fetch_articles(connection)
    # preferences = fetch_user_preferences(connection)
    #
    # results = []
    # for _, pref_row in preferences.iterrows():
    #     user_id = pref_row['user_id']
    #     user_keywords = pref_row['keywords']
    #     user_paragraph = pref_row['paragraph']
    #
    #     for _, article_row in articles.iterrows():
    #         article_content = article_row['content']
    #         relevance_score = calculate_relevance_score(user_keywords, user_paragraph, article_content)
    #         results.append({
    #             'user_id': user_id,
    #             'article_id': article_row['article_id'],
    #             'relevance_score': relevance_score
    #         })
    #
    # return jsonify(results)


    # if __name__ == "__main__":
    # print("Scraping Logistics Manager:")
    # logistics_articles = scrape_logistics_manager()
    # for article in logistics_articles:
    #     insert_article_to_db(article)
    
    # print("\nScraping World Cargo News:")
    # world_cargo_articles = scrape_world_cargo_news()
    # for article in world_cargo_articles:
    #     insert_article_to_db(article)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
