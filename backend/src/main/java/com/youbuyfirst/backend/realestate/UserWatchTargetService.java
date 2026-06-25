package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.UserWatchTargetRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.Set;

@Service
public class UserWatchTargetService {

    private static final Set<String> ALLOWED_TARGET_TYPES = Set.of("region", "complex");

    private final UserWatchTargetRepository repository;

    public UserWatchTargetService(UserWatchTargetRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<UserWatchTarget> list(String userId) {
        return repository.findByUserIdOrderByUpdatedAtDescCreatedAtDesc(userId);
    }

    @Transactional
    public SaveResult save(String userId, UserWatchTargetRequest request) {
        String targetType = normalizeTargetType(request.targetType());
        String targetId = normalizeRequired(request.targetId(), "targetId");
        String displayName = normalizeRequired(request.displayName(), "displayName");
        String landingPath = normalizeLandingPath(request.landingPath());
        Instant now = Instant.now();

        return repository.findByUserIdAndTargetTypeAndTargetId(userId, targetType, targetId)
                .map(existing -> {
                    existing.update(displayName, landingPath, now);
                    return new SaveResult(repository.save(existing), false);
                })
                .orElseGet(() -> new SaveResult(repository.save(UserWatchTarget.create(
                        userId,
                        targetType,
                        targetId,
                        displayName,
                        landingPath,
                        now
                )), true));
    }

    @Transactional
    public void remove(String userId, String targetType, String targetId) {
        repository.deleteByUserIdAndTargetTypeAndTargetId(
                userId,
                normalizeTargetType(targetType),
                normalizeRequired(targetId, "targetId")
        );
    }

    private static String normalizeTargetType(String value) {
        String normalized = normalizeRequired(value, "targetType").toLowerCase(Locale.ROOT);
        if (!ALLOWED_TARGET_TYPES.contains(normalized)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unsupported watch target type");
        }
        return normalized;
    }

    private static String normalizeLandingPath(String value) {
        String normalized = normalizeRequired(value, "landingPath");
        if (!normalized.startsWith("/realestate/") || normalized.startsWith("//")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Watch target landing path must be a real estate app path");
        }
        return normalized;
    }

    private static String normalizeRequired(String value, String fieldName) {
        String normalized = value == null ? "" : value.trim();
        if (normalized.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, fieldName + " is required");
        }
        return normalized;
    }

    public record SaveResult(UserWatchTarget target, boolean created) {
    }
}
