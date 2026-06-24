package com.youbuyfirst.backend.auth;

import java.util.Locale;

final class AuthSupport {

    private AuthSupport() {
    }

    static String normalizeUsername(String username) {
        if (username == null) {
            return "";
        }
        return username.trim().toLowerCase(Locale.ROOT);
    }

    static String normalizeEmail(String email) {
        if (email == null) {
            return "";
        }
        return email.trim().toLowerCase(Locale.ROOT);
    }

    static String normalizeDisplayName(String displayName) {
        if (displayName == null) {
            return "";
        }
        return displayName.trim();
    }
}
