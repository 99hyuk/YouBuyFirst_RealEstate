package com.youbuyfirst.backend.realestate.batch;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface RealEstateBatchUpdatePublisher {

    SseEmitter subscribe();

    void publish(RealEstateBatchUpdateEvent event);
}
