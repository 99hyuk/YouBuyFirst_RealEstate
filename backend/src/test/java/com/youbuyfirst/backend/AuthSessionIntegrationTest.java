package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class AuthSessionIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void registersUserAndUsesSessionCookieForCurrentUser() throws Exception {
        ResponseEntity<String> register = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer01",
                        "email", "observer-register@example.com",
                        "password", "watch-1234!",
                        "displayName", "Market Observer"
                ),
                String.class
        );

        assertThat(register.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        JsonNode registerBody = objectMapper.readTree(register.getBody());
        assertThat(registerBody.path("username").asText()).isEqualTo("observer01");
        assertThat(registerBody.path("email").asText()).isEqualTo("observer-register@example.com");
        assertThat(registerBody.path("displayName").asText()).isEqualTo("Market Observer");
        assertThat(registerBody.has("password")).isFalse();

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.COOKIE, sessionCookieHeader(register));
        ResponseEntity<String> me = restTemplate.exchange(
                "/api/auth/me",
                HttpMethod.GET,
                new HttpEntity<>(headers),
                String.class
        );

        assertThat(me.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode meBody = objectMapper.readTree(me.getBody());
        assertThat(meBody.path("username").asText()).isEqualTo("observer01");
        assertThat(meBody.path("email").asText()).isEqualTo("observer-register@example.com");
        assertThat(meBody.path("displayName").asText()).isEqualTo("Market Observer");
    }

    @Test
    void rejectsCurrentUserWithoutSession() {
        ResponseEntity<String> me = restTemplate.getForEntity("/api/auth/me", String.class);

        assertThat(me.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void reportsOAuthProvidersAsUnavailableWhenClientCredentialsAreMissing() throws Exception {
        ResponseEntity<String> providers = restTemplate.getForEntity("/api/auth/oauth/providers", String.class);

        assertThat(providers.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(providers.getBody());
        assertThat(body).hasSize(3);
        assertThat(body.findValuesAsText("provider")).containsExactly("google", "naver", "kakao");
        assertThat(body.findValuesAsText("displayName")).containsExactly("Google", "Naver", "Kakao");
        assertThat(body.findValues("configured")).allSatisfy(configured ->
                assertThat(configured.asBoolean()).isFalse()
        );
        assertThat(body.findValuesAsText("authorizationUrl")).containsExactly(
                "/oauth2/authorization/google",
                "/oauth2/authorization/naver",
                "/oauth2/authorization/kakao"
        );
    }

    @Test
    void logsInWithPasswordAndInvalidatesSessionOnLogout() throws Exception {
        restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer02",
                        "email", "observer-login@example.com",
                        "password", "watch-1234!",
                        "displayName", "Login Observer"
                ),
                String.class
        );

        ResponseEntity<String> login = restTemplate.postForEntity(
                "/api/auth/login",
                Map.of(
                        "username", "observer02",
                        "password", "watch-1234!"
                ),
                String.class
        );

        assertThat(login.getStatusCode()).isEqualTo(HttpStatus.OK);
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.COOKIE, sessionCookieHeader(login));

        ResponseEntity<String> logout = restTemplate.exchange(
                "/api/auth/logout",
                HttpMethod.POST,
                new HttpEntity<>(headers),
                String.class
        );
        ResponseEntity<String> meAfterLogout = restTemplate.exchange(
                "/api/auth/me",
                HttpMethod.GET,
                new HttpEntity<>(headers),
                String.class
        );

        assertThat(logout.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        assertThat(meAfterLogout.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void rejectsInvalidPasswordWithoutSessionCookie() {
        restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer03",
                        "email", "observer-bad-password@example.com",
                        "password", "watch-1234!",
                        "displayName", "Bad Password"
                ),
                String.class
        );

        ResponseEntity<String> login = restTemplate.postForEntity(
                "/api/auth/login",
                Map.of(
                        "username", "observer03",
                        "password", "wrong-password"
                ),
                String.class
        );

        assertThat(login.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(sessionCookieHeaders(login)).isEmpty();
    }

    @Test
    void rejectsDuplicateUsernameEmailAndDisplayName() {
        restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer04",
                        "email", "observer-duplicate@example.com",
                        "password", "watch-1234!",
                        "displayName", "Duplicate Observer"
                ),
                String.class
        );

        ResponseEntity<String> duplicateUsername = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer04",
                        "email", "observer-duplicate-username@example.com",
                        "password", "watch-1234!",
                        "displayName", "Other Observer"
                ),
                String.class
        );
        ResponseEntity<String> duplicateEmail = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer05",
                        "email", "OBSERVER-DUPLICATE@example.com",
                        "password", "watch-1234!",
                        "displayName", "Email Observer"
                ),
                String.class
        );
        ResponseEntity<String> duplicateDisplayName = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer06",
                        "email", "observer-duplicate-display@example.com",
                        "password", "watch-1234!",
                        "displayName", " Duplicate Observer "
                ),
                String.class
        );

        assertThat(duplicateUsername.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(duplicateEmail.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(duplicateDisplayName.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
    }

    @Test
    void rejectsInvalidUsernameAndWeakPassword() {
        ResponseEntity<String> invalidUsername = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "bad-id",
                        "email", "observer-invalid-username@example.com",
                        "password", "watch-1234!",
                        "displayName", "Invalid Username Observer"
                ),
                String.class
        );
        ResponseEntity<String> weakPassword = restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", "observer07",
                        "email", "observer-weak-password@example.com",
                        "password", "password1",
                        "displayName", "Weak Password Observer"
                ),
                String.class
        );

        assertThat(invalidUsername.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(weakPassword.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    private static String sessionCookieHeader(ResponseEntity<String> response) {
        return sessionCookieHeaders(response)
                .stream()
                .map(cookie -> cookie.split(";", 2)[0])
                .findFirst()
                .orElseThrow(() -> new AssertionError("No JSESSIONID cookie returned"));
    }

    private static List<String> sessionCookieHeaders(ResponseEntity<String> response) {
        return response.getHeaders()
                .getOrEmpty(HttpHeaders.SET_COOKIE)
                .stream()
                .filter(cookie -> cookie.startsWith("JSESSIONID="))
                .toList();
    }
}
