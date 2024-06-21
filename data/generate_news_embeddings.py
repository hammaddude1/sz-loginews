from sentence_transformers import SentenceTransformer
from transformers import BartTokenizer, BartForConditionalGeneration
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from sqlalchemy.pool import NullPool
from sklearn.metrics.pairwise import cosine_similarity
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from dotenv import load_dotenv
load_dotenv()

def db_connection():
    print("Connecting to the database")
    server = 'tep-db-test.database.windows.net,1433'
    database = 'logistics-news-aggregator-db'
    connection_string = "mssql+pyodbc:///?odbc_connect=" + quote_plus(
    "Driver={ODBC Driver 17 for SQL Server};"
    f"Server=tcp:{server},1433;"
    f"Database={database};"
    f"Uid={os.getenv('DB_USERNAME')};"
    f"Pwd={os.getenv('DB_PASSWORD')};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=1800;"
    )
    engine = create_engine(connection_string, poolclass=NullPool)
    return engine

# Load Sentence-BERT model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


# Load BART model and tokenizer for summarization
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
summarization_model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

def get_key_phrases_from_db():
    print("Fetching key phrases from the database")
    engine = db_connection()
    with engine.connect() as conn:
        key_phrases = conn.execute(text('SELECT keyphrase FROM [lng].[keyphrases]')).fetchall()[0][0]
        # Convert the comma-separated string to a Python list
    keyphrases_list = key_phrases.split(', ')
    return keyphrases_list

def get_logistics_news_by_id(article_ids):
    print("Fetching article from the database")
    engine = db_connection()
    query = f'SELECT id, news_text, website_url FROM lng.logistics_news_articles WHERE id IN ({article_ids})'
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)
    return df

# Function to get embeddings
def get_sbert_embedding(text):
    return model.encode(text, convert_to_tensor=True)

# Fetch articles from the database
def fetch_articles():
    print("Fetching articles from the database")
    engine = db_connection()
    with engine.connect() as conn:
        articles = conn.execute(text('SELECT id, news_text FROM lng.logistics_news_articles'))
        articles = [(article[0], article[1]) for article in articles]  # Extract values from the result
    return articles

# Find matches based on cosine similarity
def find_matches(article_embeddings, key_phrase_embeddings, threshold):
    matches = []
    for article_id, article_emb in article_embeddings.items():
        for phrase, phrase_emb in key_phrase_embeddings.items():
            # Move tensors to CPU and convert to NumPy arrays
            article_emb_np = article_emb.cpu().detach().numpy().reshape(1, -1)
            phrase_emb_np = phrase_emb.cpu().detach().numpy().reshape(1, -1)
            similarity = cosine_similarity(article_emb_np, phrase_emb_np)
            if similarity > threshold:
                matches.append((article_id, phrase, similarity.item()))
    if len(matches) == 0:
        print("No matches found")
    return matches

# Function to generate summary
def generate_summary(text, max_length=200):
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = summarization_model.generate(inputs, max_length=max_length, min_length=100, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def fetch_news_details_for_user():
    connection = db_connection()
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
    with connection.connect() as connection:
        df = pd.read_sql(text(query), connection)
    return df

def send_email(recipient_email, subject, articles):
    # Load the HTML template
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    # Load the HTML template from a file
    with open('backend/email_template.html', 'r') as file:
        email_template = file.read()

    # Create a Jinja2 Template object
    template = Template(email_template)

    # Render the template with article data
    html_body = template.render(articles=articles)

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'html'))

    # try:
    server = smtplib.SMTP('smtp.office365.com', 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_USER, recipient_email, text)
    server.quit()
    print(f"Email sent to {recipient_email}")

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
        send_email(email, "Daily Logistics News Update", email_body)

# Store matches in the database
def generate_matches():
    articles = fetch_articles()
    print(len(articles))
    key_phrases = get_key_phrases_from_db()
    # Fetch embeddings
    article_embeddings = {article[0]: get_sbert_embedding(article[1]) for article in articles}
    key_phrase_embeddings = {phrase: get_sbert_embedding(phrase) for phrase in key_phrases}

    threshold=os.getenv("SIMILARITY_THRESHOLD")
    matches = find_matches(article_embeddings, key_phrase_embeddings, round(float(threshold), 2))
    print("Matches found: ", len(matches))
    ids = [match[0] for match in matches]
    keywords = [match[1].strip() for match in matches]
    ids_str = ', '.join(map(str, ids))
    articles_df = get_logistics_news_by_id(ids_str)
    # Apply the generate_summary function to the news_text column
    articles_df['summary'] = articles_df['news_text'].apply(generate_summary)
    articles_df.drop(['news_text'], axis=1, inplace=True)
    articles_df.rename(columns={'id': 'logistics_news_id'}, inplace=True)
    # Add the keywords to the DataFrame
    articles_df['keywords'] = keywords
    articles_df['update_ts'] = datetime.now()
    print(articles_df)
    engine = db_connection()
    with engine.connect() as connection:
        with connection.begin() as transaction:
            articles_df.to_sql('parsed_news', connection, schema='lng', if_exists='append', index=False)
            print("Matches stored in the database")
            # Explicitly commit the transaction
            transaction.commit()



def run():
    #generate_matches()
    email = "shivendra@shipzero.com"
    send_notifications_to_user(email)


run()