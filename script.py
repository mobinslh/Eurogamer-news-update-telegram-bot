import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from telegram import Bot
from telegram.error import TelegramError
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set your Telegram Bot API token and chat ID
API_TOKEN = '8439532920:AAGUhPqG9GS-ilyj1yOiPAYlc21bR7k6Uwg'
CHAT_ID = '484750060'

# Create a bot instance
bot = Bot(token=API_TOKEN)

# Store already sent articles' links to avoid duplicates
sent_articles = set()

# Flag to skip sending on first run
first_run = True

def get_new_articles():
    """Scrape Eurogamer for new articles"""
    try:
        url = 'https://www.eurogamer.net/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Try multiple selectors as website structure may vary
        # Looking for article links in common Eurogamer structures
        article_elements = soup.find_all('article')
        
        if not article_elements:
            logger.warning("No articles found with 'article' tag")
            return []
        
        logger.info(f"Found {len(article_elements)} article elements")
        
        for article in article_elements:
            # Try to find the title and link
            link_tag = article.find('a', href=True)
            
            if link_tag:
                title_element = link_tag.find(['h2', 'h3', 'h4']) or link_tag
                title = title_element.get_text(strip=True)
                link = link_tag['href']
                
                # Make sure link is absolute
                if link.startswith('/'):
                    link = 'https://www.eurogamer.net' + link
                elif not link.startswith('http'):
                    link = 'https://www.eurogamer.net/' + link
                
                # Skip if already sent
                if link not in sent_articles and title:
                    articles.append((title, link))
                    sent_articles.add(link)
                    logger.info(f"New article found: {title[:50]}...")
        
        return articles
        
    except requests.RequestException as e:
        logger.error(f"Error fetching Eurogamer: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def send_telegram_message(articles):
    """Send articles to Telegram"""
    for title, link in articles:
        try:
            message = f"📰 *New Article*\n\n{title}\n\n{link}"
            bot.send_message(
                chat_id=CHAT_ID, 
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            logger.info(f"Sent: {title[:50]}...")
            time.sleep(1)  # Rate limiting
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            # Try without markdown if it fails
            try:
                message = f"📰 New Article\n\n{title}\n\n{link}"
                bot.send_message(chat_id=CHAT_ID, text=message)
            except:
                logger.error("Failed to send message even without markdown")

def job():
    """Main job function"""
    global first_run
    
    logger.info("Checking for new articles...")
    articles = get_new_articles()
    
    if first_run:
        logger.info(f"First run: Found {len(articles)} articles, marking as seen but not sending")
        first_run = False
        return
    
    if articles:
        logger.info(f"Found {len(articles)} new articles to send")
        send_telegram_message(articles)
    else:
        logger.info("No new articles found")

if __name__ == '__main__':
    logger.info('Starting Eurogamer news scraper for Telegram...')
    logger.info(f'Checking every 5 minutes')
    
    # Test the bot connection
    try:
        # Simple test - try to get chat info
        bot.get_chat(chat_id=CHAT_ID)
        logger.info(f"Bot connected successfully")
    except TelegramError as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        exit(1)
    
    # Run initial check (won't send messages)
    job()
    
    # Main loop - check every 5 minutes
    while True:
        try:
            time.sleep(300)  # 5 minutes
            job()
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying
