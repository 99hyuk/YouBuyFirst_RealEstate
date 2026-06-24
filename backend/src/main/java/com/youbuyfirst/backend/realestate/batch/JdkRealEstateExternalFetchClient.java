package com.youbuyfirst.backend.realestate.batch;

import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class JdkRealEstateExternalFetchClient implements RealEstateExternalFetchClient {

    private final HttpClient httpClient;

    public JdkRealEstateExternalFetchClient() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
    }

    @Override
    public RealEstateExternalFetchResult fetch(String url) {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(20))
                .header("User-Agent", "YouBuyFirst-RealEstateBot/0.1 (+newsroom and schedule link checker)")
                .GET()
                .build();
        return send(request);
    }

    @Override
    public RealEstateExternalFetchResult postForm(String url, Map<String, String> form, Map<String, String> headers) {
        String body = form.entrySet().stream()
                .map(entry -> "%s=%s".formatted(
                        encode(entry.getKey()),
                        encode(entry.getValue())
                ))
                .collect(Collectors.joining("&"));
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("User-Agent", "YouBuyFirst-RealEstateBot/0.1 (+official market data refresh)")
                .header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
        headers.forEach(builder::header);
        return send(builder.build());
    }

    private RealEstateExternalFetchResult send(HttpRequest request) {
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 200 && response.statusCode() < 400) {
                return new RealEstateExternalFetchResult(true, response.statusCode(), response.body(), null);
            }
            return RealEstateExternalFetchResult.failed(response.statusCode(), "provider returned " + response.statusCode());
        } catch (IOException exc) {
            return RealEstateExternalFetchResult.failed(0, exc.getMessage());
        } catch (InterruptedException exc) {
            Thread.currentThread().interrupt();
            return RealEstateExternalFetchResult.failed(0, "interrupted");
        }
    }

    private static String encode(String value) {
        return URLEncoder.encode(value == null ? "" : value, StandardCharsets.UTF_8);
    }
}
