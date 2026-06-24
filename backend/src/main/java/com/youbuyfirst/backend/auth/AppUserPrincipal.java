package com.youbuyfirst.backend.auth;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;

public class AppUserPrincipal implements UserDetails {

    private final String userId;
    private final String username;
    private final String email;
    private final String displayName;
    private final String passwordHash;
    private final String status;
    private final List<GrantedAuthority> authorities;

    private AppUserPrincipal(AppUser user) {
        this.userId = user.getId();
        this.username = user.getUsername();
        this.email = user.getEmail();
        this.displayName = user.getDisplayName();
        this.passwordHash = user.getPasswordHash();
        this.status = user.getStatus();
        this.authorities = List.of(new SimpleGrantedAuthority("ROLE_" + user.getRole()));
    }

    public static AppUserPrincipal from(AppUser user) {
        return new AppUserPrincipal(user);
    }

    public String getUserId() {
        return userId;
    }

    public String getEmail() {
        return email;
    }

    public String getAppUsername() {
        return username;
    }

    public String getDisplayName() {
        return displayName;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return passwordHash;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return "active".equals(status);
    }
}
