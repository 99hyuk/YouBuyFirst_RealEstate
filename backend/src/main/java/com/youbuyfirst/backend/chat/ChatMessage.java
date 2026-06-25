package com.youbuyfirst.backend.chat;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "chat_messages")
public class ChatMessage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", length = 36)
    private String userId;

    @Column(name = "session_id", length = 96)
    private String sessionId;

    @Column(name = "author_display_name", nullable = false, length = 20)
    private String authorDisplayName;

    @Column(nullable = false, length = 500)
    private String body;

    @Column(name = "attachment_json", columnDefinition = "TEXT")
    private String attachmentJson;

    @Column(nullable = false, length = 20)
    private String category;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected ChatMessage() {
    }

    private ChatMessage(String userId, String sessionId, String authorDisplayName, String body, String attachmentJson, Instant createdAt) {
        this.userId = userId;
        this.sessionId = sessionId;
        this.authorDisplayName = authorDisplayName;
        this.body = body;
        this.attachmentJson = attachmentJson;
        this.category = "chat";
        this.createdAt = createdAt;
    }

    public static ChatMessage create(String userId, String sessionId, String authorDisplayName, String body, String attachmentJson, Instant createdAt) {
        return new ChatMessage(userId, sessionId, authorDisplayName, body, attachmentJson, createdAt);
    }

    public Long getId() {
        return id;
    }

    public String getUserId() {
        return userId;
    }

    public String getSessionId() {
        return sessionId;
    }

    public String getAuthorDisplayName() {
        return authorDisplayName;
    }

    public String getBody() {
        return body;
    }

    public String getAttachmentJson() {
        return attachmentJson;
    }

    public String getCategory() {
        return category;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
