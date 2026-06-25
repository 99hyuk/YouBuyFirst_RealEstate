package com.youbuyfirst.backend.chat;

import jakarta.servlet.http.HttpSessionEvent;
import jakarta.servlet.http.HttpSessionListener;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Component
public class ChatPresenceCounter implements HttpSessionListener {

    private static final Duration DEFAULT_HEARTBEAT_TTL = Duration.ofSeconds(45);

    private final Clock clock;
    private final Duration heartbeatTtl;
    private final ConcurrentMap<String, Instant> chatSessionLastSeen = new ConcurrentHashMap<>();

    public ChatPresenceCounter() {
        this(Clock.systemUTC(), DEFAULT_HEARTBEAT_TTL);
    }

    ChatPresenceCounter(Clock clock, Duration heartbeatTtl) {
        this.clock = clock;
        this.heartbeatTtl = heartbeatTtl;
    }

    @Override
    public void sessionCreated(HttpSessionEvent event) {
    }

    @Override
    public void sessionDestroyed(HttpSessionEvent event) {
        chatSessionLastSeen.remove(event.getSession().getId());
    }

    public int markPresent(String sessionId) {
        chatSessionLastSeen.put(sessionId, Instant.now(clock));
        return activeChatSessionCount();
    }

    public int activeChatSessionCount() {
        purgeExpiredSessions();
        return chatSessionLastSeen.size();
    }

    private void purgeExpiredSessions() {
        Instant cutoff = Instant.now(clock).minus(heartbeatTtl);
        chatSessionLastSeen.entrySet().removeIf(entry -> entry.getValue().isBefore(cutoff));
    }
}
