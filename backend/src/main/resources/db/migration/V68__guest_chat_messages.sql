ALTER TABLE chat_messages
    MODIFY user_id VARCHAR(36) NULL;

ALTER TABLE chat_messages
    ADD COLUMN session_id VARCHAR(96) NULL;

CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);
