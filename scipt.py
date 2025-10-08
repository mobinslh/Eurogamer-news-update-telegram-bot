import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
from telegram import Bot
import schedule

# Set your Telegram Bot API token and chat ID
API_TOKEN = 'your_telegram_bot_api_token'  # Replace with your bot's API token
CHAT_ID = 'your_chat_id'  # Replace with your Telegram chat ID

# Create a bot instance
bot = Bot(token=API_TOKEN)

# Set the timezone for your location (UTC)
TIMEZONE = pytz.UTC

# Store already sent articles' links to avoid duplicates
sent_articles = set()

# Function to get the Eurogamer news
def get_new_articles():
    url = 'https://www.eurogamer.net/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = []

    # Find articles, assuming their timestamps are present in the <article> tag
    for article in soup.find_all('article'):
        title_tag = article.find('a', {'class': 'article-link'})
        if title_tag:
            title = title_tag.get_text()
            link = title_tag['href']
            timestamp = article.find('time')
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp['datetime'])

                # If the article has not been sent before, add it to the list
                if link not in sent_articles:
                    articles.append((title, link))
                    sent_articles.add(link)

    return articles

# Function to send a message to Telegram
def send_telegram_message(articles):
    for title, link in articles:
        message = f"{title}\n{link}"
        bot.send_message(chat_id=CHAT_ID, text=message)

# Function that will run continuously and send new articles
def job():
    articles = get_new_articles()
    if articles:
        send_telegram_message(articles)
    else:
        print("No new articles found.")

# Schedule the job to check for new articles every minute
schedule.every(1).minute.do(job)

# Run the scheduler forever
if __name__ == '__main__':
    print('Starting the Eurogamer news scraper for Telegram...')
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for a minute before checking again
