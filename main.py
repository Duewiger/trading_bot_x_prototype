import sqlite3
import requests
import logging
from environs import Env
import openai
from pybit.unified_trading import HTTP

env = Env()
env.read_env()

TRADE_VOLUME = 100
DB_FILE = "tweets.db"

X_BEARER_TOKEN = env.str("X_BEARER_TOKEN")
OPENAI_API_KEY = env.str("OPENAI_API_KEY")
BYBIT_TESTNET_PUBLIC_KEY = env.str("BYBIT_TESTNET_PUBLIC_KEY")
BYBIT_TESTNET_PRIVATE_KEY = env.str("BYBIT_TESTNET_PRIVATE_KEY")

session = HTTP(
    testnet=True,
    api_key=BYBIT_TESTNET_PUBLIC_KEY,
    api_secret=BYBIT_TESTNET_PRIVATE_KEY,
    logging_level="DEBUG"
)

balance = session.get_wallet_balance(accountType="UNIFIED", coin="USD")
print("Testnet-Guthaben:", balance)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")


def initialize_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                username TEXT,
                text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def fetch_and_store_tweets(username):
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    user_response = requests.get(user_url, headers=headers)

    if user_response.status_code == 200:
        user_id = user_response.json()["data"]["id"]
        logging.info(f"Nutzer-ID abgerufen: {user_id}")

        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        tweets_response = requests.get(tweets_url, headers=headers)

        if tweets_response.status_code == 200:
            tweets_data = tweets_response.json()
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                for tweet in tweets_data["data"]:
                    tweet_id = tweet["id"]
                    tweet_text = tweet["text"]
                    cursor.execute("""
                        INSERT OR IGNORE INTO tweets (id, username, text)
                        VALUES (?, ?, ?)
                    """, (tweet_id, username, tweet_text))
                    conn.commit()
                    logging.info(f"Tweet gespeichert: {tweet_text}")
        else:
            logging.error(f"Fehler beim Abrufen der Tweets: {tweets_response.status_code}")
    else:
        logging.error(f"Fehler beim Abrufen der Nutzer-ID: {user_response.status_code}")


def analyze_tweet_with_chatgpt(tweet_text):
    messages = [
        {"role": "system", "content": "Du bist ein Assistent, der Texte analysiert und Kaufempfehlungen für Kryptowährungen identifiziert."},
        {"role": "user", "content": f"Analysiere den folgenden Text und bestimme, ob er eine klare Kaufempfehlung für eine Kryptowährung oder Aktie enthält:\n\n"
                                    f"\"{tweet_text}\"\n\n"
                                    "Wenn ja, gib das Symbol der empfohlenen Kryptowährung als gültiges Handelspaar auf ByBit zurück als Antwort, ohne weiteren Text, ohne Trennzeichen. Wenn nein, antworte mit \"Keine Empfehlung\", als Antwort, ohne weiteren Text"}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"GPT-Antwort: {result}")
        return result if result != "Keine Empfehlung" else None
    except Exception as e:
        logging.error(f"Fehler bei der Analyse des Tweets: {e}")
        return None


def execute_trade(platform, coin, volume, trail_stop, leverage):
    order = session.place_order(
        category="spot",
        symbol=coin,
        side="Buy",
        order_type="Market",
        qty=0.1,
        time_in_force="GoodTillCancel"
    )

    print("Order-Details:", order)

    if coin:
        logging.info(f"Handel ausgeführt: {coin} auf {platform}")
        logging.info(f"Volumen: {volume}, Trailing Stop: {trail_stop}, Hebel: {leverage}")
    else:
        logging.info("Kein Handel ausgeführt: Keine gültige Empfehlung.")

    open_orders = session.get_active_order(symbol=coin)
    print("Aktive Orders:", open_orders)

    order_history = session.get_order_history(symbol=coin)
    print("Order-Historie:", order_history)


def main():
    username = input("Bitte gib den Nutzernamen ein: ")
    initialize_db()
    fetch_and_store_tweets(username)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, text FROM tweets")
        tweets = cursor.fetchall()

        for tweet_id, tweet_text in tweets:
            logging.info(f"Analysiere Tweet: {tweet_text}")
            recommendation = analyze_tweet_with_chatgpt(tweet_text)

            if recommendation:
                logging.info(f"Empfohlene Kryptowährung: {recommendation}")
                execute_trade("Bybit", recommendation, TRADE_VOLUME, trail_stop=0.1, leverage=10)
            else:
                logging.info("Keine gültige Empfehlung gefunden.")


if __name__ == "__main__":
    main()