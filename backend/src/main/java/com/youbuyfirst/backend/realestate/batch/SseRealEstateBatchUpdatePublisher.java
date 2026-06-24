package com.youbuyfirst.backend.realestate.batch;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

@Component
public class SseRealEstateBatchUpdatePublisher implements RealEstateBatchUpdatePublisher {

    private static final long STREAM_TIMEOUT_MILLIS = 30 * 60 * 1000L;
    private static final String UPDATE_EVENT_NAME = "realestate-batch-update";

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    @Override
    public SseEmitter subscribe() {
        SseEmitter emitter = new SseEmitter(STREAM_TIMEOUT_MILLIS);
        emitters.add(emitter);
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        emitter.onError(error -> emitters.remove(emitter));
        sendConnectedEvent(emitter);
        return emitter;
    }

    @Override
    public void publish(RealEstateBatchUpdateEvent event) {
        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event()
                        .name(UPDATE_EVENT_NAME)
                        .data(event));
            } catch (IOException | IllegalStateException error) {
                emitters.remove(emitter);
                emitter.completeWithError(error);
            }
        }
    }

    private void sendConnectedEvent(SseEmitter emitter) {
        try {
            emitter.send(SseEmitter.event()
                    .name("realestate-batch-connected")
                    .data(Map.of(
                            "status", "connected",
                            "connectedAt", Instant.now().toString()
                    )));
        } catch (IOException | IllegalStateException error) {
            emitters.remove(emitter);
            emitter.completeWithError(error);
        }
    }
}
