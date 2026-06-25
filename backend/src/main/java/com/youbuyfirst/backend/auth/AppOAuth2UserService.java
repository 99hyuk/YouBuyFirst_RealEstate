package com.youbuyfirst.backend.auth;

import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

@Service
public class AppOAuth2UserService implements OAuth2UserService<OAuth2UserRequest, OAuth2User> {

    private final DefaultOAuth2UserService delegate = new DefaultOAuth2UserService();
    private final OAuthAccountService oauthAccountService;

    public AppOAuth2UserService(OAuthAccountService oauthAccountService) {
        this.oauthAccountService = oauthAccountService;
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oauthUser = delegate.loadUser(userRequest);
        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        OAuthProviderProfile profile = OAuthProviderProfile.from(registrationId, oauthUser.getAttributes());
        AppUser user = oauthAccountService.findOrCreateUser(profile);
        return AppUserPrincipal.oauth(user, oauthUser.getAttributes());
    }
}
