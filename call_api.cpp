// call_api.cpp

#include <iostream>
#include <string>
#include <curl/curl.h>
#include "json.hpp"

using json = nlohmann::json;

/*
(참고) ollama api 서버 응답의 예시:

```json
{
    "robot1": "회피",
    "robot2": "회피",
    "robot3": "회피",
    "description": "robot3의 지뢰탐지기가 지뢰 발견 시, 지뢰 제거 도구가 없기에 우회로를 통해 회피. 모든 로봇은 안전을 위해 함께 회피한다."
}
```

두번째 예시:

```json
{
    "robot1": "소총",
    "robot2": "소총",
    "robot3": "대기",
    "description": "피격 상황 발생 및 소규모 적 병사 조우 시, robot1과 robot2는 소총으로 대응하고, robot3은 현재 과업 대기."
}
```

*/

// libcurl 콜백: 서버 응답을 std::string에 저장
static size_t WriteCallback(void *contents, size_t size, size_t nmemb, void *userp)
{
    size_t total = size * nmemb;
    static_cast<std::string *>(userp)->append(static_cast<char *>(contents), total);
    return total;
}

const std::string BASE_URL = "http://172.28.80.1:8888";

void test_ollama()
{
    std::cout << "test 1: /ollama_test\n";
    std::cout << "===========================\n";

    CURL *curl = curl_easy_init();
    if (!curl)
    {
        std::cerr << "curl 초기화 실패\n";
        return;
    }

    std::string response;
    // URL에 쿼리 파라미터 추가
    std::string url = BASE_URL + "/ollama_test?prompt=just%20say%20hi";

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK)
    {
        std::cerr << "에러 발생: " << curl_easy_strerror(res) << "\n";
    }
    else
    {
        try
        {
            auto j = json::parse(response);
            std::cout << "response:\n"
                      << j.at("response").get<std::string>() << "\n";
        }
        catch (const std::exception &e)
        {
            std::cerr << "JSON 파싱 에러: " << e.what() << "\n";
        }
    }

    curl_easy_cleanup(curl);
}

void test_command()
{
    std::cout << "\ntest 2: /command (LLM‑based decision)\n";
    std::cout << "======================================\n";

    // Python과 동일한 구조의 JSON 객체 생성
    json battle_state = {
        {"robot_availability", {{"robot1", true}, {"robot2", true}, {"robot3", true}}},
        {"robot_equipment", {{"robot1", {{"대전차 무장", 2}, {"소총 무장", 2}, {"통신중계기", 1}}}, {"robot2", {{"소총 무장", 2}, {"통신중계기", 1}}}, {"robot3", {{"소총 무장", 1}, {"지뢰탐지기", 2}, {"통신중계기", 1}}}}},
        {"enemy_size", {{"적 전차", 0}, {"적 병사", 0}}},
        {"battlefield_info", {{"우회로 여부", true}, {"피격 여부", false}, {"적 지뢰 여부", true}}},
        {"possible_responses", json::array({"소총", "대전차", "통신중계기", "회피", "대기", "기존 과업"})}};

    // payload = {"state": battle_state}
    json payload = {{"state", battle_state}};
    std::string payload_str = payload.dump();

    CURL *curl = curl_easy_init();
    if (!curl)
    {
        std::cerr << "curl 초기화 실패\n";
        return;
    }

    std::string response;
    std::string url = BASE_URL + "/command";

    struct curl_slist *headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload_str.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, payload_str.size());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK)
    {
        std::cerr << "에러 발생: " << curl_easy_strerror(res) << "\n";
    }
    else
    {
        try
        {
            auto j = json::parse(response);
            // Python 코드처럼 ```json ... ``` 마커 처리
            std::string raw = j.at("response").get<std::string>();
            const std::string marker = "```json";
            if (raw.rfind(marker, 0) == 0)
            {
                raw = raw.substr(marker.size());
                if (raw.size() >= 3 && raw.substr(raw.size() - 3) == "```")
                    raw = raw.substr(0, raw.size() - 3);
            }
            auto parsed = json::parse(raw);
            std::cout << "parsed response:\n"
                      << parsed.dump(4) << "\n";
        }
        catch (const std::exception &e)
        {
            std::cerr << "JSON 파싱 에러: " << e.what() << "\n";
            std::cout << "원본 응답:\n"
                      << response << "\n";
        }
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}

int main()
{
    curl_global_init(CURL_GLOBAL_DEFAULT);
    test_ollama();
    test_command();
    curl_global_cleanup();
    return 0;
}
