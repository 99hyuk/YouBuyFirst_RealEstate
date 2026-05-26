package com.youbuyfirst.backend.instrument;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Set;

@Service
public class InstrumentAliasReviewService {

    private static final Set<String> REVIEW_STATUSES = Set.of("SUGGESTED", "REJECTED");

    private final InstrumentAliasCandidateRepository aliasCandidateRepository;
    private final InstrumentAliasRepository aliasRepository;
    private final InstrumentRepository instrumentRepository;

    public InstrumentAliasReviewService(
            InstrumentAliasCandidateRepository aliasCandidateRepository,
            InstrumentAliasRepository aliasRepository,
            InstrumentRepository instrumentRepository
    ) {
        this.aliasCandidateRepository = aliasCandidateRepository;
        this.aliasRepository = aliasRepository;
        this.instrumentRepository = instrumentRepository;
    }

    @Transactional
    public InstrumentAliasCandidate reviewCandidate(Long candidateId, String status, String reviewer, String reviewNotes) {
        InstrumentAliasCandidate candidate = findCandidate(candidateId);
        if ("PROMOTED".equals(candidate.getStatus())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "promoted alias candidate cannot be reviewed");
        }

        String normalizedStatus = normalizeStatus(status);
        if (!REVIEW_STATUSES.contains(normalizedStatus)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported alias candidate review status: " + status);
        }

        candidate.markReviewed(normalizedStatus, clean(reviewer), clean(reviewNotes), Instant.now());
        return candidate;
    }

    @Transactional
    public InstrumentAlias promoteCandidate(Long candidateId, Double confidence, String reviewer, String reviewNotes) {
        InstrumentAliasCandidate candidate = findCandidate(candidateId);
        if (!"SUGGESTED".equals(candidate.getStatus())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "alias candidate must be suggested before promotion");
        }
        if (isBlank(candidate.getSuggestedMarket()) || isBlank(candidate.getSuggestedSymbol())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "alias candidate needs suggested market and symbol before promotion");
        }

        Instrument instrument = instrumentRepository
                .findByMarketIgnoreCaseAndSymbolIgnoreCase(candidate.getSuggestedMarket(), candidate.getSuggestedSymbol())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "suggested instrument not found"));

        List<InstrumentAlias> acceptedAliases = aliasRepository.findByNormalizedAliasAndStatusIgnoreCaseAndAmbiguousFalse(
                candidate.getNormalizedAlias(),
                "ACCEPTED"
        );
        for (InstrumentAlias alias : acceptedAliases) {
            if (!alias.getInstrument().getId().equals(instrument.getId())) {
                throw new ResponseStatusException(HttpStatus.CONFLICT, "alias is already accepted for another instrument");
            }
        }
        InstrumentAlias existingAcceptedAlias = acceptedAliases.stream()
                .filter(alias -> alias.getInstrument().getId().equals(instrument.getId()))
                .findFirst()
                .orElse(null);

        Instant now = Instant.now();
        String reviewerValue = clean(reviewer);
        String reviewNotesValue = clean(reviewNotes);
        candidate.markPromoted(reviewerValue, reviewNotesValue, now);

        if (existingAcceptedAlias != null) {
            return existingAcceptedAlias;
        }
        return aliasRepository.save(new InstrumentAlias(
                instrument,
                candidate.getAlias(),
                "alias-candidate:" + candidate.getSource(),
                confidence == null ? 0.8 : confidence,
                "ACCEPTED",
                false,
                reviewNotesValue,
                now
        ));
    }

    private InstrumentAliasCandidate findCandidate(Long candidateId) {
        return aliasCandidateRepository.findById(candidateId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "alias candidate not found"));
    }

    private static String normalizeStatus(String status) {
        if (isBlank(status)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "status is required");
        }
        return status.trim().toUpperCase();
    }

    private static String clean(String value) {
        if (isBlank(value)) {
            return null;
        }
        return value.trim();
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
