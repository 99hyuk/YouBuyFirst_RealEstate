package com.youbuyfirst.backend.chat;

import com.youbuyfirst.backend.auth.AppUserPrincipal;
import com.youbuyfirst.backend.chat.dto.ChatMessageRequest;
import com.youbuyfirst.backend.chat.dto.ChatMessageResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;

@RestController
@RequestMapping("/api/chat/messages")
public class ChatMessageController {

    private final ChatMessageService service;
    private final ChatMessageStream stream;

    public ChatMessageController(ChatMessageService service, ChatMessageStream stream) {
        this.service = service;
        this.stream = stream;
    }

    @GetMapping
    public List<ChatMessageResponse> recent(
            @RequestParam(defaultValue = "100") int limit,
            Authentication authentication,
            HttpServletRequest request
    ) {
        return service.recent(limit, currentUserId(authentication), currentSessionId(request, false));
    }

    @GetMapping(path = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        return stream.open();
    }

    @PostMapping
    public ResponseEntity<ChatMessageResponse> create(
            @AuthenticationPrincipal AppUserPrincipal principal,
            HttpServletRequest servletRequest,
            @Valid @RequestBody ChatMessageRequest request
    ) {
        return ResponseEntity.status(201).body(service.create(principal, currentSessionId(servletRequest, true), request));
    }

    private static String currentUserId(Authentication authentication) {
        if (authentication == null || !(authentication.getPrincipal() instanceof AppUserPrincipal principal)) {
            return null;
        }
        return principal.getUserId();
    }

    private static String currentSessionId(HttpServletRequest request, boolean create) {
        var session = request.getSession(create);
        return session == null ? null : session.getId();
    }
}
