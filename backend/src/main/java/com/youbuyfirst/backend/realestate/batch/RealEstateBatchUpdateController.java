package com.youbuyfirst.backend.realestate.batch;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
public class RealEstateBatchUpdateController {

    private final RealEstateBatchUpdatePublisher publisher;

    public RealEstateBatchUpdateController(RealEstateBatchUpdatePublisher publisher) {
        this.publisher = publisher;
    }

    @GetMapping(value = "/api/realestate/batch-updates/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        return publisher.subscribe();
    }
}
