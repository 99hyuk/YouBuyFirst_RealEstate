package com.youbuyfirst.backend.chat;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.auth.AppUserRepository;
import com.youbuyfirst.backend.auth.AppUserPrincipal;
import com.youbuyfirst.backend.chat.dto.ChatMessageAttachment;
import com.youbuyfirst.backend.chat.dto.ChatMessageRequest;
import com.youbuyfirst.backend.chat.dto.ChatMessageResponse;
import com.youbuyfirst.backend.chat.dto.ChatNicknameAvailabilityResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Service
public class ChatMessageService {

    private static final int MAX_LIMIT = 100;
    private static final int DEFAULT_LIMIT = MAX_LIMIT;

    private final ChatMessageRepository repository;
    private final ChatMessageStream stream;
    private final ObjectMapper objectMapper;
    private final AppUserRepository appUserRepository;

    public ChatMessageService(
            ChatMessageRepository repository,
            ChatMessageStream stream,
            ObjectMapper objectMapper,
            AppUserRepository appUserRepository
    ) {
        this.repository = repository;
        this.stream = stream;
        this.objectMapper = objectMapper;
        this.appUserRepository = appUserRepository;
    }

    @Transactional
    public ChatMessageResponse create(AppUserPrincipal principal, String currentSessionId, ChatMessageRequest request) {
        String body = normalizeBody(request.body());
        String currentUserId = principal == null ? null : principal.getUserId();
        String fallbackDisplayName = principal == null ? "손님" : principal.getDisplayName();
        String displayName = normalizeDisplayName(request.displayName(), fallbackDisplayName);
        if (principal == null && appUserRepository.existsByDisplayName(displayName)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Chat display name is already registered");
        }
        ChatMessageAttachment attachment = normalizeAttachment(request.attachment());
        Instant now = Instant.now();

        ChatMessage message = repository.save(ChatMessage.create(
                currentUserId,
                currentSessionId,
                displayName,
                body,
                serializeAttachment(attachment),
                now
        ));

        ChatMessageResponse response = ChatMessageResponse.from(message, currentUserId, currentSessionId, now, attachment);
        broadcastAfterCommit(response);
        return response;
    }

    @Transactional(readOnly = true)
    public List<ChatMessageResponse> recent(int limit, String currentUserId, String currentSessionId) {
        Instant now = Instant.now();
        List<ChatMessage> newestFirst = repository.findAll(PageRequest.of(
                0,
                normalizedLimit(limit),
                Sort.by(Sort.Order.desc("createdAt"), Sort.Order.desc("id"))
        )).getContent();

        List<ChatMessage> chronological = new ArrayList<>(newestFirst);
        java.util.Collections.reverse(chronological);

        return chronological.stream()
                .map(message -> ChatMessageResponse.from(
                        message,
                        currentUserId,
                        currentSessionId,
                        now,
                        deserializeAttachment(message.getAttachmentJson())
                ))
                .toList();
    }

    @Transactional(readOnly = true)
    public ChatNicknameAvailabilityResponse nicknameAvailability(String displayName) {
        String normalized = normalizeGuestDisplayNameCandidate(displayName);
        return new ChatNicknameAvailabilityResponse(!appUserRepository.existsByDisplayName(normalized));
    }

    private static int normalizedLimit(int limit) {
        if (limit <= 0) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_LIMIT);
    }

    private static String normalizeBody(String value) {
        String normalized = value == null ? "" : value.trim();
        if (normalized.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat message body is required");
        }
        if (normalized.length() > 500) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat message body is too long");
        }
        return normalized;
    }

    private static String normalizeDisplayName(String requestedDisplayName, String fallbackDisplayName) {
        String normalized = requestedDisplayName == null ? "" : requestedDisplayName.trim();
        if (normalized.isEmpty()) {
            normalized = fallbackDisplayName;
        }
        if (normalized.length() > 20) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat display name is too long");
        }
        return normalized;
    }

    private static String normalizeGuestDisplayNameCandidate(String value) {
        String normalized = trimOptional(value);
        if (normalized == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat display name is required");
        }
        if (normalized.length() > 20) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat display name is too long");
        }
        return normalized;
    }

    private ChatMessageAttachment normalizeAttachment(ChatMessageAttachment attachment) {
        if (attachment == null) {
            return null;
        }

        String type = trimRequired(attachment.type(), "Chat attachment type is required");
        if (!type.equals("region") && !type.equals("complex")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat attachment type is not supported");
        }

        String targetId = trimRequired(attachment.targetId(), "Chat attachment target is required");
        String title = trimRequired(attachment.title(), "Chat attachment title is required");
        String landingPath = trimRequired(attachment.landingPath(), "Chat attachment landing path is required");
        if (!landingPath.startsWith("/realestate/") || landingPath.startsWith("//") || hasLineBreak(landingPath)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat attachment landing path is not supported");
        }

        String metricTone = trimOptional(attachment.metricTone());
        if (metricTone != null && !metricTone.equals("up") && !metricTone.equals("down") && !metricTone.equals("flat")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat attachment metric tone is not supported");
        }

        return new ChatMessageAttachment(
                type,
                targetId,
                title,
                trimOptional(attachment.subtitle()),
                trimOptional(attachment.metricLabel()),
                trimOptional(attachment.metricValue()),
                metricTone,
                landingPath
        );
    }

    private String serializeAttachment(ChatMessageAttachment attachment) {
        if (attachment == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(attachment);
        } catch (JsonProcessingException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Chat attachment could not be stored");
        }
    }

    private ChatMessageAttachment deserializeAttachment(String attachmentJson) {
        if (attachmentJson == null || attachmentJson.isBlank()) {
            return null;
        }
        try {
            return objectMapper.readValue(attachmentJson, ChatMessageAttachment.class);
        } catch (JsonProcessingException ex) {
            return null;
        }
    }

    private static String trimRequired(String value, String message) {
        String normalized = trimOptional(value);
        if (normalized == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
        }
        return normalized;
    }

    private static String trimOptional(String value) {
        String normalized = value == null ? "" : value.trim();
        return normalized.isEmpty() ? null : normalized;
    }

    private static boolean hasLineBreak(String value) {
        return value.contains("\n") || value.contains("\r");
    }

    private void broadcastAfterCommit(ChatMessageResponse response) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            stream.broadcast(response);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                stream.broadcast(response);
            }
        });
    }
}
