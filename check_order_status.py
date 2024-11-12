# check_order_status.py

import requests
import os
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

# 주문 uuid를 여기에 입력하여 실행하세요.
check_order_status("0db8b520-c8ff-4b2e-9b51-a49e6d911628")
