# ollama-api-study

- pip install fastapi uvicorn requests
- uvicorn app:app --host 0.0.0.0 --port 8888
- sudo apt update -y; sudo apt install libcurl4-openssl-dev -y
- g++ -o call_api call_api.cpp -lcurl


request example:

```
curl -X POST http://localhost:8000/command \
     -H "Content-Type: application/json" \
     -d '{
           "state": {
             "robot_availability": {"robot1": true, "robot2": true, "robot3": true},
             "robot_equipment": {
               "robot1": {"대전차 무장": 2, "소총 무장": 2, "통신중계기": 1},
               "robot2": {"소총 무장": 2, "통신중계기": 1},
               "robot3": {"소총 무장": 1, "지뢰탐지기": 2, "통신중계기": 1}
             },
             "enemy_size": {"적 전차": 0, "적 병사": 0},
             "battlefield_info": {"우회로 여부": true, "피격 여부": false, "적 지뢰 여부": true},
             "possible_responses": ["소총","대전차","지뢰탐지기","통신중계기","회피","대기","기존 과업"]
           }
         }'

```