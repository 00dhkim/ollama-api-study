import requests

# FastAPI 서버 주소
url = "http://localhost:8888/chat"
params = {
    "prompt": "just say hi"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    result = response.json()
    print("응답:", result.get("response"))
else:
    print("에러 발생:", response.status_code, response.text)
