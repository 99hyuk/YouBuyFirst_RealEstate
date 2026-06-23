package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;

/**
 * 카카오 로컬 키워드 검색으로 단지 문자열을 좌표로 변환한다.
 * REST 키가 비어있으면 비활성(빈 결과)으로 동작한다.
 */
@Component
public class KakaoGeocodeClient {

    private static final Logger log = LoggerFactory.getLogger(KakaoGeocodeClient.class);
    private static final String ENDPOINT = "https://dapi.kakao.com/v2/local/search/keyword.json";

    private final String restApiKey;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public KakaoGeocodeClient(@Value("${app.realestate.kakao.rest-api-key:}") String restApiKey) {
        this.restApiKey = restApiKey == null ? "" : restApiKey.trim();
    }

    public boolean isEnabled() {
        return !restApiKey.isBlank();
    }

    /** 좌표를 찾으면 [lat, lng], 못 찾거나 비활성이면 empty. */
    public Optional<double[]> geocode(String query) {
        if (!isEnabled() || query == null || query.isBlank()) {
            return Optional.empty();
        }
        try {
            String url = ENDPOINT + "?size=1&query=" + URLEncoder.encode(query.trim(), StandardCharsets.UTF_8);
            HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                    .header("Authorization", "KakaoAK " + restApiKey)
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                return Optional.empty();
            }
            JsonNode documents = objectMapper.readTree(response.body()).path("documents");
            if (!documents.isArray() || documents.isEmpty()) {
                return Optional.empty();
            }
            JsonNode first = documents.get(0);
            double lng = Double.parseDouble(first.path("x").asText());
            double lat = Double.parseDouble(first.path("y").asText());
            if (!Double.isFinite(lat) || !Double.isFinite(lng)) {
                return Optional.empty();
            }
            return Optional.of(new double[]{lat, lng});
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return Optional.empty();
        } catch (Exception e) {
            log.debug("kakao geocode failed for query={}", query, e);
            return Optional.empty();
        }
    }
}
