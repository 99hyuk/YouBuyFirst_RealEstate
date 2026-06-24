package com.youbuyfirst.backend.realestate.batch;

import java.time.Instant;

public record RealEstateBatchUpdateEvent(
        String topic,
        String month,
        int acceptedItems,
        Instant refreshedAt
) {
}
