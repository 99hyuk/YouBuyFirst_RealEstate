package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.auth.AppUserPrincipal;
import com.youbuyfirst.backend.realestate.dto.UserWatchTargetListResponse;
import com.youbuyfirst.backend.realestate.dto.UserWatchTargetRequest;
import com.youbuyfirst.backend.realestate.dto.UserWatchTargetResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/realestate/watch-targets")
public class UserWatchTargetController {

    private final UserWatchTargetService service;

    public UserWatchTargetController(UserWatchTargetService service) {
        this.service = service;
    }

    @GetMapping
    public UserWatchTargetListResponse list(Authentication authentication) {
        return new UserWatchTargetListResponse(
                service.list(currentUserId(authentication)).stream()
                        .map(UserWatchTargetResponse::from)
                        .toList()
        );
    }

    @PostMapping
    public ResponseEntity<UserWatchTargetResponse> save(
            Authentication authentication,
            @Valid @RequestBody UserWatchTargetRequest request
    ) {
        UserWatchTargetService.SaveResult result = service.save(currentUserId(authentication), request);
        return ResponseEntity
                .status(result.created() ? HttpStatus.CREATED : HttpStatus.OK)
                .body(UserWatchTargetResponse.from(result.target()));
    }

    @DeleteMapping
    public ResponseEntity<Void> remove(
            Authentication authentication,
            @RequestParam String targetType,
            @RequestParam String targetId
    ) {
        service.remove(currentUserId(authentication), targetType, targetId);
        return ResponseEntity.noContent().build();
    }

    private static String currentUserId(Authentication authentication) {
        if (authentication == null || !(authentication.getPrincipal() instanceof AppUserPrincipal principal)) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User session is required");
        }
        return principal.getUserId();
    }
}
