package com.youbuyfirst.backend.realestate.batch;

import java.time.Instant;

public record RealEstateBatchJobRunResponse(
        String jobName,
        String status,
        String exitCode,
        String month,
        Instant startedAt,
        Instant endedAt
) {
}
