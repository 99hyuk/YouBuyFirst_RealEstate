package com.youbuyfirst.backend.auth;

import com.youbuyfirst.backend.auth.dto.RegisterRequest;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;

@Service
public class AuthService {

    private final AppUserRepository repository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(AppUserRepository repository, PasswordEncoder passwordEncoder) {
        this.repository = repository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public AppUser register(RegisterRequest request) {
        String username = AuthSupport.normalizeUsername(request.username());
        String email = AuthSupport.normalizeEmail(request.email());
        String displayName = AuthSupport.normalizeDisplayName(request.displayName());
        if (repository.existsByUsername(username)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Username already registered");
        }
        if (repository.existsByEmail(email)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Email already registered");
        }
        if (repository.existsByDisplayName(displayName)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Display name already registered");
        }

        Instant now = Instant.now();
        AppUser user = AppUser.local(username, email, displayName, passwordEncoder.encode(request.password()), now);
        return repository.save(user);
    }

    @Transactional
    public AppUser markSeen(String userId) {
        AppUser user = findById(userId);
        user.markSeen(Instant.now());
        return user;
    }

    @Transactional(readOnly = true)
    public AppUser findById(String userId) {
        return repository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User session is no longer valid"));
    }
}
