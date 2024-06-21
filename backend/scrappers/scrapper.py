import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from db.connection import connect_to_db, insert_article_to_db, remove_duplicate_articles


BATCH_SIZE = 15

def fetch_article_text(url):
    response = requests.get(url)
    if response.status_code != 200:
        return ""
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find('div', class_='entry-content').find_all('p')
    news_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
    return news_text


def scrape_logistics_manager():
    base_urls = [
        "https://www.logisticsmanager.com/logistics/",
        "https://www.logisticsmanager.com/intralogistics/",
        "https://www.logisticsmanager.com/supply-chain/",
        "https://www.logisticsmanager.com/property/",
        "https://www.logisticsmanager.com/corporate-insight/",
        "https://www.logisticsmanager.com/events-news/"
    ]
    BATCH_SIZE = 100
    articles = []
    visited_urls = set()

    for base_url in base_urls:
        page = 1
        while True:
            url = f"{base_url}page/{page}/"
            print(f"Fetching: {url}")  # Added logging
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to retrieve {url}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = soup.find_all('article')

            if not article_elements:
                print(f"No articles found on {url}")
                break

            new_articles_found = False
            for article in article_elements:
                title_tag = article.find('h2')
                date_tag = article.find('time')
                link_tag = article.find('a')

                if title_tag and date_tag and link_tag:
                    news_url = link_tag['href']
                    if news_url in visited_urls:
                        continue  # Avoid duplicates
                    visited_urls.add(news_url)

                    title = title_tag.get_text(strip=True)
                    news_datetime = datetime.fromisoformat(date_tag['datetime'])
                    news_text = fetch_article_text(news_url)

                    articles.append({
                        'title': title,
                        'news_datetime': news_datetime,
                        'fetch_datetime': datetime.now(),
                        'news_text': news_text,
                        'website_url': news_url
                    })

                    new_articles_found = True

                    if len(articles) >= BATCH_SIZE:
                        insert_article_to_db(articles)
                        remove_duplicate_articles()  # Remove duplicates after insertion
                        articles = []  # Reset the list after insertion

            if not new_articles_found:
                print(f"No new articles found on {url}, stopping pagination.")
                break

            page += 1

    # Insert any remaining articles
    if articles:
        insert_article_to_db(articles)
        remove_duplicate_articles()  # Remove duplicates after insertion

    return articles



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


def scrape_dvz():
    base_url = "https://www.dvz.de/"
    page = 1
    articles = []

    # Fetch existing URLs from the database
    # existing_urls = fetch_existing_urls()

    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_date = yesterday.date()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while True:
        url = f"{base_url}page/{page}/"
        response = requests.get(url, headers=headers)
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
                if news_datetime.date() != yesterday_date:
                    # Skip articles not from yesterday
                    continue

                news_url = link_tag['href']
                # if news_url in existing_urls:
                #     # Skip duplicate articles
                #     continue

                title = title_tag.get_text(strip=True)
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

    return articles




def scrape_dvz_zero():
    base_url = "https://www.dvz.de/zero/"
    page = 1
    articles = []

    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_date = yesterday.date()

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
                if news_datetime.date() != yesterday_date:
                    # Stop processing if the article is not from yesterday
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
