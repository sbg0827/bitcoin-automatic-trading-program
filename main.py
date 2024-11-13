import requests
import os
import time
import pandas as pd
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
SERVER_URL = 'https://api.upbit.com'

# 비트코인 시세 조회 함수
def get_btc_price():
    url = f"{SERVER_URL}/v1/ticker"
    querystring = {"markets": "KRW-BTC"}
    response = requests.get(url, params=querystring)
    data = response.json()
    return data[0]['trade_price'] if data else None

# 원화 잔고 조회 함수
def get_krw_balance():
    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4())
    }

    jwt_token = jwt.encode(payload, SECRET_KEY)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(f"{SERVER_URL}/v1/accounts", headers=headers)
    accounts = response.json()

    for account in accounts:
        if account['currency'] == 'KRW':
            return float(account['balance'])  # 원화 잔고 반환
    return 0  # 원화 잔고가 없는 경우 0 반환

# 비트코인 잔고 조회 함수
def get_btc_balance():
    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4())
    }

    jwt_token = jwt.encode(payload, SECRET_KEY)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(f"{SERVER_URL}/v1/accounts", headers=headers)
    accounts = response.json()

    for account in accounts:
        if account['currency'] == 'BTC':
            return float(account['balance'])  # BTC 잔고 반환
    return 0  # BTC 잔고가 없는 경우 0 반환

# 주문 상태 확인 함수
def check_order_status(order_uuid):
    query = {'uuid': order_uuid}
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, SECRET_KEY)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(f"{SERVER_URL}/v1/order", params=query, headers=headers)
    print("주문 상태 확인 응답:", response.json())
    return response.json()

# 매수 함수 (원화 잔고 확인 추가)
def buy_order():
    krw_balance = get_krw_balance()  # 원화 잔고 확인

    # 매수 금액이 원화 잔고보다 많으면 주문을 실행하지 않음
    if krw_balance < 100000:  # 매수 금액보다 잔고가 부족하면 종료
        print("매수할 원화 잔고가 부족합니다.")
        return None  # 잔고 부족 시 매수 실행하지 않음

    query = {
        'market': 'KRW-BTC',
        'side': 'bid',
        'price': '150000',  # 매수 금액 설정 (원화 기준)
        'ord_type': 'price',  # 시장가 매수
    }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, SECRET_KEY)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.post(f"{SERVER_URL}/v1/orders", params=query, headers=headers)
    data = response.json()
    print("매수 주문 응답:", data)
    return data.get("uuid")  # uuid 반환

# 매도 함수 (uuid 반환)
def sell_order():
    btc_balance = get_btc_balance()  # 현재 BTC 잔고 조회

    if btc_balance <= 0:
        print("매도할 비트코인이 부족합니다.")
        return  # 잔고가 없으면 매도 실행하지 않음

    query = {
        'market': 'KRW-BTC',
        'side': 'ask',
        'volume': str(btc_balance),  # 잔고에 맞춰 매도 수량 설정
        'ord_type': 'market',
    }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, SECRET_KEY)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.post(f"{SERVER_URL}/v1/orders", params=query, headers=headers)
    data = response.json()
    print("매도 주문 응답:", data)
    return data.get("uuid")  # uuid 반환

# 주문 체결 상태 주기적으로 확인 함수
def monitor_order(order_uuid):
    while True:
        order_status = check_order_status(order_uuid)
        state = order_status.get("state")
        if state == "done":
            print("주문이 체결되었습니다.")
            break
        elif state == "wait":
            print("주문 대기 중... 다시 확인합니다.")
        else:
            print(f"주문 상태: {state}")
            break
        time.sleep(10)  # 10초 대기 후 다시 확인

# 1분마다 업비트에서 가격 데이터를 수집하고, 5개와 20개의 이동평균을 계산하는 함수
def fetch_price_data():
    prices = []
    while True:
        price = get_btc_price()  # 현재 비트코인 가격 조회
        if price is not None:
            prices.append(price)
            if len(prices) > 20:  # 데이터를 20개로 제한
                prices.pop(0)
            print(f"현재 가격: {price}")
        
        # 데이터가 충분히 쌓이면 이동평균 계산
        if len(prices) >= 20:
            df = pd.DataFrame(prices, columns=['price'])
            short_ma = df['price'].rolling(window=5).mean().iloc[-1]
            long_ma = df['price'].rolling(window=20).mean().iloc[-1]
            
            # 매수, 매도 조건 확인
            if short_ma > long_ma:
                print("매수 조건 충족")
                order_uuid = buy_order()  # 매수 함수 호출 및 uuid 반환
                if order_uuid:
                    monitor_order(order_uuid)  # 주문 상태 모니터링
            elif short_ma < long_ma:
                print("매도 조건 충족")
                order_uuid = sell_order()  # 매도 함수 호출 및 uuid 반환
                if order_uuid:
                    monitor_order(order_uuid)  # 주문 상태 모니터링
            else:
                print("매매 조건 없음")
        
        # 1분 대기
        time.sleep(60)

# 데이터 수집 및 매매 전략 실행
fetch_price_data()
