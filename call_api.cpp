#include <iostream>
#include <string>
#include <curl/curl.h>

// 서버로부터 받은 데이터를 버퍼에 저장하기 위한 콜백 함수
size_t WriteCallback(void *contents, size_t size, size_t nmemb, void *userp)
{
    std::string *response = static_cast<std::string *>(userp);
    size_t totalSize = size * nmemb;
    response->append(static_cast<char *>(contents), totalSize);
    return totalSize;
}

int main()
{
    CURL *curl;
    CURLcode res;
    std::string responseString;

    // 요청할 프롬프트 (필요에 따라 수정 가능합니다)
    std::string prompt = "just say hi";

    // FastAPI 서버의 엔드포인트 URL (여기서는 localhost:8888로 가정)
    std::string baseUrl = "http://localhost:8888/chat";

    // 전역적으로 libcurl 초기화
    curl_global_init(CURL_GLOBAL_DEFAULT);

    // curl 핸들 생성
    curl = curl_easy_init();
    if (curl)
    {
        // URL 인코딩: 쿼리 문자열의 안전한 전달을 위해 prompt를 인코딩합니다.
        char *encodedPrompt = curl_easy_escape(curl, prompt.c_str(), prompt.length());
        if (encodedPrompt)
        {
            // 최종 GET 요청할 URL 생성
            std::string url = baseUrl + "?prompt=" + std::string(encodedPrompt);
            curl_free(encodedPrompt); // 인코딩된 문자열 해제

            // libcurl 옵션 설정
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            // 응답 데이터를 저장할 콜백 함수 지정
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &responseString);
            // 요청 타임아웃(초 단위)
            curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);

            // GET 요청 실행
            res = curl_easy_perform(curl);
            if (res != CURLE_OK)
            {
                std::cerr << "curl_easy_perform() 실패: " << curl_easy_strerror(res) << std::endl;
            }
            else
            {
                std::cout << "서버 응답:" << std::endl;
                std::cout << responseString << std::endl;
            }
        }
        else
        {
            std::cerr << "URL 인코딩에 실패했습니다." << std::endl;
        }
        // curl 핸들 정리
        curl_easy_cleanup(curl);
    }
    else
    {
        std::cerr << "curl 초기화에 실패했습니다." << std::endl;
    }

    // 전역 libcurl 정리
    curl_global_cleanup();
    return 0;
}
