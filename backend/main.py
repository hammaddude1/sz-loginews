import time
import os
from flask import Flask, jsonify, request
from db.connection import connect_to_db, fetch_articles, fetch_user_preferences, insert_user_keyphrases, remove_duplicate_articles
from dotenv import load_dotenv
from scrappers.scrapper import scrape_logistics_manager, scrape_world_cargo_news, scrape_dvz_zero, scrape_dvz
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import pyodbc
from jinja2 import Environment, FileSystemLoader


load_dotenv()
PASSKEY = os.getenv('DB_PASSKEY')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

def fetch_news_details_for_user():
    connection = connect_to_db()
    query = """
        SELECT
    logistics_news_id,
    summary,
    keywords,
    website_url,
    update_ts
    FROM
        [lng].[parsed_news]
    WHERE
        update_ts = (SELECT MAX(update_ts) FROM [lng].[parsed_news]);
    """
    df = pd.read_sql(query, connection)
    print(df)
    connection.close()
    return df

def send_email(recipient_email, subject, articles):
    # Load the HTML template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('email_template.html')

    # Render the template with article data
    html_body = template.render(articles=articles)

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'html'))

    # try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_USER, recipient_email, text)
    server.quit()
    print(f"Email sent to {recipient_email}")
    # except Exception as e:
    #     print(f"Failed to send email to {recipient_email}: {str(e)}")


def send_notifications_to_user(email):
    news_details = fetch_news_details_for_user()
    print(news_details)
    for index, row in news_details.iterrows():
        email_body = f"""
        Summary: {row['summary']}
        Keywords: {row['keywords']}
        URL: {row['website_url']}
        """
        print(email_body)
        send_email(row['email'], "Daily Logistics News Update", email_body)

@app.route('/add_user_keyphrases', methods=['POST'])
def add_user_keyphrases():
    # try:
    data = request.get_json()
    email = data.get('email')
    passkey = data.get('passkey')

    if passkey != PASSKEY:
        return jsonify({"error": "Invalid passkey"}), 403

    # If email is provided, add the user
    if email:
        insert_user_keyphrases(email)
        send_notifications_to_user(email)

    return jsonify({"message": "Notification sent to the new user successfully"}), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

@app.route('/keyphrases', methods=['GET'])
def get_keyphrases():
    connection = connect_to_db()
    cursor = connection.cursor()
    query = "SELECT keyphrase FROM [lng].[keyphrases]"
    cursor.execute(query)
    keyphrases = cursor.fetchall()
    cursor.close()
    connection.close()

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
