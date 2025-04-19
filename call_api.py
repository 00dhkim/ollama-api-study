import requests
import json

BASE_URL = "http://localhost:8888"


def test_ollama():
    """GET /ollama_test — 서버‑Ollama 연결 확인"""
    print("test 1: /ollama_test")
    print("===========================")

    try:
        r = requests.get(
            f"{BASE_URL}/ollama_test",
            params={"prompt": "just say hi"},
            timeout=30,
        )
        r.raise_for_status()
        
        print("response:")
        print(r.json().get("response"))
        
    except requests.RequestException as e:
        print("에러 발생:", e)


def test_command():
    """GET /command — 전장 상태 입력으로 LLM 명령 생성"""
    print("\ntest 2: /command (LLM‑based decision)")
    print("======================================")

    # 전장 정보
    battle_state = {
        "robot_availability": {
            "robot1": True,
            "robot2": True,
            "robot3": True,
        },
        "robot_equipment": {
            "robot1": {
                "대전차 무장": 2,
                "소총 무장": 2,
                "통신중계기": 1,
            },
            "robot2": {
                "소총 무장": 2,
                "통신중계기": 1,
            },
            "robot3": {
                "소총 무장": 1,
                "지뢰탐지기": 2,
                "통신중계기": 1,
            },
        },
        "enemy_size": {
            "적 전차": 0,
            "적 병사": 0,
        },
        "battlefield_info": {
            "우회로 여부": True,
            "피격 여부": False,
            "적 지뢰 여부": True,
        },
        "possible_responses": [
            "소총",
            "대전차",
            "통신중계기",
            "회피",
            "대기",
            "기존 과업",
        ],
    }

    payload = {"state": battle_state}

    try:
        print("request:")
        print(battle_state)
        r = requests.post(f"{BASE_URL}/command", json=payload, timeout=30)
        r.raise_for_status()
        # print("응답:", r.json())
        
        # pasre response
        raw_str = r.json().get("response").strip()
        if raw_str.startswith("```json"):
            raw_str = raw_str[len("```json") : -len("```")].strip()
        parsed_json = json.loads(raw_str)  # validate json
        
        print("parsed response:")
        print(parsed_json)
        
    except requests.RequestException as e:
        print("에러 발생:", e)


if __name__ == "__main__":
    test_ollama()
    test_command()
