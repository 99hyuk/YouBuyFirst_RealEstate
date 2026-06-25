package com.youbuyfirst.backend.auth;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserRequest;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.stereotype.Service;

@Service
public class AppOidcUserService implements OAuth2UserService<OidcUserRequest, OidcUser> {

    private final OAuth2UserService<OidcUserRequest, OidcUser> delegate;
    private final OAuthAccountService oauthAccountService;

    @Autowired
    public AppOidcUserService(OAuthAccountService oauthAccountService) {
        this(oauthAccountService, new OidcUserService());
    }

    AppOidcUserService(
            OAuthAccountService oauthAccountService,
            OAuth2UserService<OidcUserRequest, OidcUser> delegate
    ) {
        this.oauthAccountService = oauthAccountService;
        this.delegate = delegate;
    }

    @Override
    public OidcUser loadUser(OidcUserRequest userRequest) throws OAuth2AuthenticationException {
        OidcUser oidcUser = delegate.loadUser(userRequest);
        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        OAuthProviderProfile profile = OAuthProviderProfile.from(registrationId, oidcUser.getAttributes());
        AppUser user = oauthAccountService.findOrCreateUser(profile);
        return AppUserPrincipal.oidc(
                user,
                oidcUser.getAttributes(),
                oidcUser.getIdToken(),
                oidcUser.getUserInfo()
        );
    }
}
