package com.youbuyfirst.backend.auth;

import com.youbuyfirst.backend.auth.dto.OAuthProviderStatusResponse;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class OAuthProviderStatusService {

    private static final List<ProviderDefinition> PROVIDERS = List.of(
            new ProviderDefinition("google", "Google"),
            new ProviderDefinition("naver", "Naver"),
            new ProviderDefinition("kakao", "Kakao")
    );

    private final ObjectProvider<ClientRegistrationRepository> clientRegistrationRepository;

    public OAuthProviderStatusService(ObjectProvider<ClientRegistrationRepository> clientRegistrationRepository) {
        this.clientRegistrationRepository = clientRegistrationRepository;
    }

    public List<OAuthProviderStatusResponse> providers() {
        ClientRegistrationRepository registrations = clientRegistrationRepository.getIfAvailable();
        return PROVIDERS.stream()
                .map(provider -> new OAuthProviderStatusResponse(
                        provider.id(),
                        provider.displayName(),
                        authorizationUrl(provider.id()),
                        isConfigured(registrations, provider.id())
                ))
                .toList();
    }

    private static boolean isConfigured(ClientRegistrationRepository registrations, String provider) {
        return registrations != null && registrations.findByRegistrationId(provider) != null;
    }

    private static String authorizationUrl(String provider) {
        return "/oauth2/authorization/" + provider;
    }

    private record ProviderDefinition(String id, String displayName) {
    }
}
