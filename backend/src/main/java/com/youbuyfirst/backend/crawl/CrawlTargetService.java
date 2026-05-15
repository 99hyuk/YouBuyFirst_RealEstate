package com.youbuyfirst.backend.crawl;

import com.youbuyfirst.backend.crawl.dto.CrawlTargetClaimRequest;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetClaimResponse;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetCompletionRequest;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetView;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

@Service
public class CrawlTargetService {

    private static final Duration CLAIM_LEASE_DURATION = Duration.ofMinutes(5);

    private final CrawlTargetRepository crawlTargetRepository;

    public CrawlTargetService(CrawlTargetRepository crawlTargetRepository) {
        this.crawlTargetRepository = crawlTargetRepository;
    }

    @Transactional
    public CrawlTargetClaimResponse claim(CrawlTargetClaimRequest request) {
        List<String> sources = normalizeSources(request.allowedSources());
        if (sources.isEmpty()) {
            return new CrawlTargetClaimResponse(List.of());
        }

        Instant now = Instant.now();
        List<CrawlTarget> claimedTargets = crawlTargetRepository.findClaimable(
                CrawlTargetStatus.ACTIVE,
                sources,
                now,
                PageRequest.of(0, request.normalizedLimit())
        );
        claimedTargets.forEach(target -> target.claim(request.workerId().trim(), now, now.plus(CLAIM_LEASE_DURATION)));

        return new CrawlTargetClaimResponse(claimedTargets.stream()
                .map(CrawlTargetView::from)
                .toList());
    }

    @Transactional
    public void complete(String targetId, CrawlTargetCompletionRequest request) {
        Instant now = Instant.now();
        CrawlTarget target = crawlTargetRepository.findByTargetId(targetId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "crawl target not found"));

        String workerId = request.workerId().trim();
        if (target.isLeasedToAnotherWorker(workerId, now)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "crawl target is leased to another worker");
        }

        Instant finishedAt = request.finishedAt() == null ? now : request.finishedAt();
        target.markCompleted(
                request.status(),
                finishedAt,
                request.postsSeen(),
                request.postsAccepted(),
                request.backoffCategory(),
                request.backoffUntil(),
                request.backoffReason()
        );
    }

    private static List<String> normalizeSources(List<String> sources) {
        if (sources == null) {
            return List.of();
        }
        return sources.stream()
                .filter(source -> source != null && !source.isBlank())
                .map(source -> source.trim().toUpperCase())
                .distinct()
                .toList();
    }
}
