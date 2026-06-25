package com.youbuyfirst.backend.chat.dto;

import com.youbuyfirst.backend.chat.ChatMessage;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

public record ChatMessageResponse(
        String id,
        String author,
        String badge,
        String body,
        String timeLabel,
        String category,
        boolean mine,
        String tone,
        boolean verified,
        Instant createdAt,
        ChatMessageAttachment attachment
) {

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");
    private static final DateTimeFormatter OLD_MESSAGE_FORMAT = DateTimeFormatter.ofPattern("MM.dd").withZone(KST);

    public static ChatMessageResponse from(
            ChatMessage message,
            String currentUserId,
            String currentSessionId,
            Instant now,
            ChatMessageAttachment attachment
    ) {
        boolean verified = message.getUserId() != null;
        boolean mine = verified
                ? message.getUserId().equals(currentUserId)
                : message.getSessionId() != null && message.getSessionId().equals(currentSessionId);
        return new ChatMessageResponse(
                "server-chat-" + message.getId(),
                message.getAuthorDisplayName(),
                "채팅",
                message.getBody(),
                timeLabel(message.getCreatedAt(), now),
                message.getCategory(),
                mine,
                "blue",
                verified,
                message.getCreatedAt(),
                attachment
        );
    }

    private static String timeLabel(Instant createdAt, Instant now) {
        Duration age = Duration.between(createdAt, now);
        if (age.isNegative() || age.toMinutes() < 1) {
            return "방금";
        }
        if (age.toHours() < 1) {
            return age.toMinutes() + "분 전";
        }
        if (age.toHours() < 24) {
            return age.toHours() + "시간 전";
        }
        return OLD_MESSAGE_FORMAT.format(createdAt);
    }
}
