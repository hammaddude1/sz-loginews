import time
import os
from flask import Flask, jsonify, request
from db.connection import connect_to_db, fetch_articles, fetch_user_preferences, insert_user_keyphrases, remove_duplicate_articles
from dotenv import load_dotenv
from scrappers.scrapper import scrape_logistics_manager, scrape_world_cargo_news, scrape_dvz_zero, scrape_dvz
from flask_cors import CORS


load_dotenv()
PASSKEY = os.getenv('DB_PASSKEY')

# Initialize Flask app
app = Flask(__name__)
CORS(app)


@app.route('/add_user_keyphrases', methods=['POST'])
def add_user_keyphrases():
    try:
        data = request.get_json()
        email = data['email']
        # key_phrases = data['key_phrases']
        passkey = data['passkey']
        if passkey != PASSKEY:
            return jsonify({"error": "Invalid passkey"}), 403

        insert_user_keyphrases(email)
        return jsonify({"message": "User added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}),

@app.route('/keyphrases', methods=['GET'])
def get_keyphrases():
    connection = connect_to_db()
    cursor = connection.cursor()
    query = "SELECT keyphrase FROM [lng].[keyphrases]"
    cursor.execute(query)
    keyphrases = cursor.fetchall()
    cursor.close()
    connection.close()

    # Debugging: Print the fetched data
    print("Fetched keyphrases:", keyphrases)

    # Convert to a list of dictionaries
    keyphrases_list = [{'keyphrase': row[0]} for row in keyphrases]

    return jsonify(keyphrases_list)

@app.route('/process', methods=['GET'])
def process():
    remove_duplicate_articles()
    print('asdas')

    return 'hell'

    # 1
    #     logistics_articles = scrape_logistics_manager()
    #     articles_list = []
    #     for article in logistics_articles:
    #         articles_list.append(article)
    #     print(articles_list)
    #     remove_duplicate_articles()
    #     return jsonify(articles_list)
    remove_duplicate_articles()

# 2
#     logistics_articles = scrape_dvz()
#     articles_list = []
#     for article in logistics_articles:
#         print(article)
#         articles_list.append(article)
#     print(articles_list)
#     remove_duplicate_articles()
#     return jsonify(articles_list)

    # world_cargo_articles = scrape_world_cargo_news()
    # articles_list = []
    # for article in world_cargo_articles:
    #     articles_list.append(article)
    # return jsonify(articles_list)



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

#
# DELETE FROM [lng].[test_logistics_news_articles]
# WHERE CAST(news_datetime AS DATE) = '2024-06-20';
