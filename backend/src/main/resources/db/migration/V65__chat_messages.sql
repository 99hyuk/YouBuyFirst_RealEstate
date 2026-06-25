CREATE TABLE chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    author_display_name VARCHAR(20) NOT NULL,
    body VARCHAR(500) NOT NULL,
    category VARCHAR(20) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL,
    CONSTRAINT fk_chat_messages_user FOREIGN KEY (user_id) REFERENCES app_users(id)
);

CREATE INDEX idx_chat_messages_created_at ON chat_messages (created_at DESC, id DESC);
