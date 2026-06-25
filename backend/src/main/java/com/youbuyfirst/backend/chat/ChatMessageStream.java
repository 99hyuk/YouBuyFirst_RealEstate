package com.youbuyfirst.backend.chat;

import com.youbuyfirst.backend.chat.dto.ChatMessageResponse;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class ChatMessageStream {

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    public SseEmitter open() {
        SseEmitter emitter = new SseEmitter(0L);
        emitters.add(emitter);
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        emitter.onError(error -> emitters.remove(emitter));

        try {
            emitter.send(SseEmitter.event().name("ready").data("ok"));
        } catch (IOException | IllegalStateException ex) {
            removeEmitter(emitter, ex);
        }

        return emitter;
    }

    public void broadcast(ChatMessageResponse response) {
        ChatMessageResponse broadcastResponse = new ChatMessageResponse(
                response.id(),
                response.author(),
                response.badge(),
                response.body(),
                response.timeLabel(),
                response.category(),
                false,
                response.tone(),
                response.verified(),
                response.createdAt(),
                response.attachment()
        );

        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event().name("chat-message").data(broadcastResponse));
            } catch (IOException | IllegalStateException ex) {
                removeEmitter(emitter, ex);
            }
        }
    }

    private void removeEmitter(SseEmitter emitter, Exception cause) {
        emitters.remove(emitter);
        try {
            emitter.completeWithError(cause);
        } catch (RuntimeException ignored) {
            // The client may already be gone; removing the emitter is enough.
        }
    }
}
