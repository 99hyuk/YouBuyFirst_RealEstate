package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.instrument.InstrumentAliasCandidate;

import java.time.Instant;

public record InstrumentAliasCandidateView(
        Long id,
        String source,
        String alias,
        String normalizedAlias,
        String suggestedMarket,
        String suggestedSymbol,
        String reason,
        String contextSnippet,
        String sampleUrl,
        Instant firstSeenAt,
        Instant lastSeenAt,
        Integer occurrenceCount,
        String status,
        Instant createdAt,
        Instant updatedAt
) {
    public static InstrumentAliasCandidateView from(InstrumentAliasCandidate candidate) {
        return new InstrumentAliasCandidateView(
                candidate.getId(),
                candidate.getSource(),
                candidate.getAlias(),
                candidate.getNormalizedAlias(),
                candidate.getSuggestedMarket(),
                candidate.getSuggestedSymbol(),
                candidate.getReason(),
                candidate.getContextSnippet(),
                candidate.getSampleUrl(),
                candidate.getFirstSeenAt(),
                candidate.getLastSeenAt(),
                candidate.getOccurrenceCount(),
                candidate.getStatus(),
                candidate.getCreatedAt(),
                candidate.getUpdatedAt()
        );
    }
}
