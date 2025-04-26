from __future__ import annotations

import json
import os

import requests
from fastapi import FastAPI, HTTPException, Query
from contextlib import contextmanager
from pydantic import BaseModel
from typing import Dict, List

MODEL = "gemma3:latest"
OLLAMA_SERVER = "http://localhost:11434"
TIMEOUT = 30


@contextmanager
def lifespan(app: FastAPI):
    """동기 requests로 Ollama warm-up, FastAPI ≥0.110 권장 방식."""
    # ── startup ────────────────────────────────────────────────
    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={
                "model": MODEL,
                "prompt": "Testing. Just say hi and nothing else.",
                "stream": False,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        print("✅ Ollama model pre-loaded")
    except Exception as exc:
        # 실패해도 앱 전체가 죽지 않도록 로그만 남김
        print(f"⚠️  Warm-up failed: {exc}")
    yield  # ← 여기서부터 서버가 요청을 받기 시작
    # ── shutdown ───────────────────────────────────────────────
    print("👋 Lifespan shutdown complete")


app = FastAPI(lifespan=lifespan)


class BattleState(BaseModel):
    robot_availability: Dict[str, bool]
    robot_equipment: Dict[str, Dict[str, int]]
    enemy_size: Dict[str, int]
    battlefield_info: Dict[str, bool]
    possible_responses: List[str]


class ChatRequest(BaseModel):
    state: BattleState  # **유일한 필수 필드**


def build_prompt(state: BattleState) -> str:
    state_json = json.dumps(state.dict(), ensure_ascii=False, indent=2)

    prompt = (
        """당신은 군사 지휘관입니다. 보유한 로봇들로 작전을 수행하는 도중에 발생하는 돌발 상황을 대처하기 위해 로봇들에게 명령을 내려야 합니다.
로봇들은 다양한 임무장비를 보유하고 있으며, 각 임무장비는 특정 상황에 대응할 수 있는 능력을 가지고 있습니다.
로봇들은 현재 수행중인 과업에 대한 정보를 가지고 있으며, 이를 바탕으로 적 정보를 분석하여 대응방법을 결정합니다.

아래는 당신이 획득할 수 있는 전장 정보입니다. 각 정보는 다음을 의미합니다:
- robot_availability: 각 로봇이 현재 다른 임무 수행 중인지, 아니면 가용 로봇인지 나타냄.
- robot_equipment: 각 로봇이 보유한 임무장비의 목록과 현재 사용중인지 여부. 0이면 현재 다른 용도로 사용 중, 1이면 사용가능하나 계획되지않음, 2이면 기존에 계획된 장비이며 사용 가능
- enemy_size: 마주한 적의 규모
- battlefield_info: 기타 전장 정보. "적 지뢰 여부"는 현재 지뢰가 발견되었는지를 의미함.
- possible_responses: 가능한 대응 방법

다음은 권고 사항입니다:
- 적 전차가 0이면 대전차 굳이 쓸 필요 없음
- 지뢰가 없을 시 지뢰탐지기 사용할 필요 없음
- 적 지뢰를 발견하였고 회피 결정을 할 때에는 모든 로봇들이 함께 회피하여야 함


## examples

### case 1

```
{
  "robot_availability": {
    "robot1": True,
    "robot2": True,
    "robot3": True
  },
  "robot_equipment": {
    "robot1": {
      "대전차 무장": 2,
      "소총 무장": 2,
      "통신중계기": 1,
    },
    "robot2": {
      "소총 무장": 2,
      "통신중계기": 1
    },
    "robot3": {
      "소총 무장": 1,
      "지뢰탐지기": 2,
      "통신중계기": 1
    }
  },
  "enemy_size": {
    "적 전차": 0,
    "적 병사": 0
  },
  "battlefield_info": {
    "우회로 여부": True,
    "피격 여부": False,
    "적 지뢰 여부": True
  },
  "possible_responses": [
    "소총",
    "대전차",
    "지뢰탐지기",
    "통신중계기",
    "회피",
    "대기",
    "기존 과업"
  ]
}
```

```
{
    "robot1": "회피",
    "robot2": "회피",
    "robot3": "회피",
    "description": "robot3의 지뢰탐지기가 지뢰 발견 시, 지뢰 제거 도구가 없기에 우회로를 통해 회피. 모든 로봇은 안전을 위해 함께 회피한다."
}
```

### case 2

```
{
  "robot_availability": {
    "robot1": True,
    "robot2": True,
    "robot3": True
  },
  "robot_equipment": {
    "robot1": {
      "대전차 무장": 2,
      "소총 무장": 2,
      "통신중계기": 1,
    },
    "robot2": {
      "소총 무장": 2,
      "통신중계기": 1
    },
    "robot3": {
      "소총 무장": 1,
      "지뢰탐지기": 2,
      "통신중계기": 1
    }
  },
  "enemy_size": {
    "적 전차": 0,
    "적 병사": 2
  },
  "battlefield_info": {
    "우회로 여부": False,
    "피격 여부": True,
    "적 지뢰 여부": False
  },
  "possible_responses": [
    "소총",
    "대전차",
    "지뢰탐지기",
    "통신중계기",
    "회피",
    "대기",
    "기존 과업"
  ]
}
```

```
{
    "robot1": "소총",
    "robot2": "소총",
    "robot3": "대기",
    "description": "소규모 적 병사 조우 시, 기존에 계획된 robot1과 robot2의 소총으로 대응."
}
```

### case 3

```
{
  "robot_availability": {
    "robot1": True,
    "robot2": True,
    "robot3": True
  },
  "robot_equipment": {
    "robot1": {
      "대전차 무장": 2,
      "소총 무장": 2,
      "통신중계기": 1,
    },
    "robot2": {
      "소총 무장": 2,
      "통신중계기": 1
    },
    "robot3": {
      "소총 무장": 1,
      "지뢰탐지기": 2,
      "통신중계기": 1
    }
  },
  "enemy_size": {
    "적 전차": 1,
    "적 병사": 4
  },
  "battlefield_info": {
    "우회로 여부": False,
    "피격 여부": False,
    "적 지뢰 여부": False
  },
  "possible_responses": [
    "소총",
    "대전차",
    "지뢰탐지기",
    "통신중계기",
    "회피",
    "대기",
    "기존 과업"
  ]
}
```

```
{
    "robot1": "대전차",
    "robot2": "소총",
    "robot3": "소총",
    "description": "적 전차 및 대규모 적 병사 발견 시, 대전차 무장이 존재하는 robot1은 대전차로, 나머지는 소총으로 대응. robot3은 기존에 소총 무장이 계획되지 않았으나 대규모 적 대응을 위해 사용."
}
```

### case 4

```
{
  "robot_availability": {
    "robot1": False,
    "robot2": True,
    "robot3": False
  },
  "robot_equipment": {
    "robot1": {
      "대전차 무장": 2,
      "소총 무장": 2,
      "통신중계기": 1,
    },
    "robot2": {
      "소총 무장": 2,
      "통신중계기": 1
    },
    "robot3": {
      "소총 무장": 1,
      "지뢰탐지기": 2,
      "통신중계기": 1
    }
  },
  "enemy_size": {
    "적 전차": 0,
    "적 병사": 3
  },
  "battlefield_info": {
    "우회로 여부": False,
    "피격 여부": False,
    "적 지뢰 여부": False
  },
  "possible_responses": [
    "소총",
    "대전차",
    "지뢰탐지기",
    "통신중계기",
    "회피",
    "대기",
    "기존 과업"
  ]
}
```

```
{
    "robot1": "기존 과업",
    "robot2": "소총",
    "robot3": "기존 과업",
    "description": "robot1과 robot3은 기존에 발생한 교전으로 인해 가용불가능할 때, robot2만 가용하므로 새로운 적에 대응."
}
```


## 전장 정보

```"""
        + f"{state_json}"
        + """```


## 출력 양식

json 형식으로 로봇들의 대응방법을 출력합니다. 그 외의 내용은 출력하지 않습니다.

```
{
    "robot1": "[대응방법]",
    "robot2": "[대응방법]",
    "robot3": "[대응방법]",
    "description": "[설명]"
}
```"""
    )
    return prompt


@app.post("/command")
def command(req: ChatRequest):
    prompt = build_prompt(req.state)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 1,
            "repeat_penalty": 1.0,
            "seed": 42,
        },
    }

    try:
        res = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json=payload,
            timeout=TIMEOUT,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama 호출 실패: {e}") from e

    return res.json()


@app.get("/ollama_test")
def chat_get(prompt: str = Query("just say hi")):
    response = requests.post(
        f"{OLLAMA_SERVER}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=30,  # Set the timeout value in seconds
    )
    print(response.status_code, response.text)
    return response.json()


@app.get("/")
def root():
    return {"message": "Welcome to the Ollama API!"}
