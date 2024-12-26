import os
import sys
import sqlite3
import requests
import time

from pybit.unified_trading import HTTP

bitget_path = os.path.abspath("./bitget-python-sdk-api")
sys.path.append(bitget_path)

import bitget.v1.mix.order_api as maxOrderApi
import bitget.bitget_api as baseApi
from bitget.exceptions import BitgetAPIException
from bitget.client import Client

from environs import Env

env = Env()
env.read_env()

# API Configurations
X_API_KEY = env.str("X_API_KEY")
BYBIT_PUBLIC_KEY = env.str("BYBIT_PUBLIC_KEY")
BYBIT_PRIVATE_KEY = env.str("BYBIT_PRIVATE_KEY")
BITGET_API_KEY = env.str("BITGET_API_KEY")
BITGET_API_SECRET = env.str("BITGET_API_SECRET")
BITGET_API_PASSPHRASE = env.str("BITGET_API_PASSPHRASE")
TRADE_VOLUME = 100
LATENCY_LIMIT = 1


# X API Tests
X_USERNAME = env.str("X_USERNAME")
X_BEARER_TOKEN = env.str("X_BEARER_TOKEN")

x_test_url = f"https://api.x.com/2/users/by/username/{X_USERNAME}"
x_test_headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}

x_response = requests.get(url=x_test_url, headers=x_test_headers)

if x_response.status_code == 200:
    print("Erfolgreiche Antwort: ")
    print(x_response.json())
    print("\n")
else:
    print(f"Fehler: {x_response.status_code}")
    print(x_response.json())
    print("\n")


# ByBit API Tests
session = HTTP(
    testnet=False,
    api_key=BYBIT_PUBLIC_KEY,
    api_secret=BYBIT_PRIVATE_KEY,
)

response = session.get_tickers(category="spot", symbol="BTCUSDT")
print(response)
print("\n")


# Bitget API Tests
client = Client(
    api_key=BITGET_API_KEY,
    api_secret_key=BITGET_API_SECRET,
    passphrase=BITGET_API_PASSPHRASE
)

try:
    response = client._request(
        method="GET",
        request_path="/api/spot/v1/account/getInfo",
        params={}
    )
    print("Antwort von Bitget:", response)
except BitgetAPIException as e:
    print("Fehler bei der Bitget API-Anfrage:", e.message)