package com.youbuyfirst.backend.chat;

public record ChatPresenceResponse(
        int activeSessionCount,
        String source
) {
}
