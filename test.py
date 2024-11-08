import requests
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import time

# API 키와 시크릿 키 입력
ACCESS_KEY = 'dFfWItBQyNr7NUYtesWolkxwoRqDQPhqhuueTOLH'       # 업비트에서 발급받은 API 키
SECRET_KEY = 'I2CYexhZj6kmQhoqQ7ag6oYx2h4ADpqbW07pBtZo'       # 업비트에서 발급받은 시크릿 키
SERVER_URL = 'https://api.upbit.com'

# 현재 비트코인 시세 조회
def get_btc_price():
    url = f"{SERVER_URL}/v1/ticker"
    querystring = {"markets": "KRW-BTC"}
    response = requests.get(url, params=querystring)
    data = response.json()
    return data[0]['trade_price'] if data else None

# 현재 비트코인 가격 출력
btc_price = get_btc_price()
print(f"현재 KRW-BTC 가격: {btc_price}")

