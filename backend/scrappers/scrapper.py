import requests
from bs4 import BeautifulSoup
from datetime import datetime
from db.connection import connect_to_db, insert_article_to_db


# def scrape_logistics_manager():
#     url = "https://www.logisticsmanager.com/"
#     response = requests.get(url)
#     if response.status_code != 200:
#         print(f"Failed to retrieve {url}")
#         return []
#
#     soup = BeautifulSoup(response.content, 'html.parser')
#     articles = soup.find_all('article')
#
#     article_data = []
#     for article in articles:
#         title_tag = article.find('h2')
#         date_tag = article.find('time')
#         link_tag = article.find('a')
#
#         if title_tag and date_tag and link_tag:
#             title = title_tag.get_text(strip=True)
#             news_datetime = date_tag['datetime']
#             news_url = link_tag['href']
#             news_text = fetch_article_text(news_url)
#
#             article_data.append({
#                 'title': title,
#                 'news_datetime': news_datetime,
#                 'fetch_datetime': datetime.now(),
#                 'news_text': news_text,
#                 'website_url': news_url
#             })
#     return article_data

BATCH_SIZE = 15


def scrape_logistics_manager():
    base_url = "https://www.logisticsmanager.com/"
    page = 1
    articles = []

    while True:
        url = f"{base_url}page/{page}/"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        article_elements = soup.find_all('article')

        if not article_elements:
            break

        for article in article_elements:
            title_tag = article.find('h2')
            date_tag = article.find('time')
            link_tag = article.find('a')

            if title_tag and date_tag and link_tag:
                news_datetime = datetime.fromisoformat(date_tag['datetime'])
                if news_datetime.month != 6:  # Only process articles from June
                    continue

                title = title_tag.get_text(strip=True)
                news_url = link_tag['href']
                news_text = fetch_article_text(news_url)

                articles.append({
                    'title': title,
                    'news_datetime': news_datetime,
                    'fetch_datetime': datetime.now(),
                    'news_text': news_text,
                    'website_url': news_url
                })

                if len(articles) >= BATCH_SIZE:
                    insert_article_to_db(articles)
                    articles = []  # Reset the list after insertion

        page += 1

    # Insert any remaining articles
    if articles:
        insert_article_to_db(articles)


def fetch_article_text(url):
    response = requests.get(url)
    if response.status_code != 200:
        return ""
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find('div', class_='entry-content').find_all('p')
    news_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
    return news_text


def scrape_world_cargo_news():
    url = "https://www.worldcargonews.com/"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve {url}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('div', class_='news-item')

    article_data = []
    for article in articles:
        title_tag = article.find('a')
        date_tag = article.find('time')
        link_tag = article.find('a')
        
        if title_tag and date_tag and link_tag:
            title = title_tag.get_text(strip=True)
            news_datetime = date_tag['datetime']
            news_url = link_tag['href']
            news_text = fetch_article_text(news_url)
            
            article_data.append({
                'title': title,
                'news_datetime': news_datetime,
                'fetch_datetime': datetime.now(),
                'news_text': news_text,
                'website_url': news_url
            })
    return article_data

