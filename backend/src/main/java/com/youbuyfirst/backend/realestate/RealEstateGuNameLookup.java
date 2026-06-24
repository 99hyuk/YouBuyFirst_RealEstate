package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.util.Map;

/**
 * 법정동코드 → 구 명칭. 프론트(front/src/fixtures/transaction-browse-seed.json의 guCentroids)와
 * 같은 이름을 써야 사전 적재 배치가 만드는 쿼리 문자열이 실시간 캐시 키와 일치한다.
 */
@Component
public class RealEstateGuNameLookup {

    private static final String FALLBACK_NAME = "서울";

    private final Map<String, String> namesByLegalDongCode;

    public RealEstateGuNameLookup(ObjectMapper objectMapper) {
        this.namesByLegalDongCode = load(objectMapper);
    }

    public String nameFor(String legalDongCode) {
        if (legalDongCode == null) {
            return FALLBACK_NAME;
        }
        return namesByLegalDongCode.getOrDefault(legalDongCode, FALLBACK_NAME);
    }

    private static Map<String, String> load(ObjectMapper objectMapper) {
        try (InputStream stream = new ClassPathResource("realestate/gu-centroids.json").getInputStream()) {
            return objectMapper.readValue(stream, new TypeReference<Map<String, String>>() {
            });
        } catch (IOException e) {
            return Map.of();
        }
    }
}
