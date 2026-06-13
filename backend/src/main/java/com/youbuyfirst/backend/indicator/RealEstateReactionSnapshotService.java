package com.youbuyfirst.backend.indicator;

import com.youbuyfirst.backend.realestate.RealEstateTarget;
import com.youbuyfirst.backend.realestate.RealEstateTargetGraphService;
import com.youbuyfirst.backend.realestate.RealEstateTargetRepository;
import com.youbuyfirst.backend.realestate.RealEstateTimelineService;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;

@Service
public class RealEstateReactionSnapshotService {

    private static final String FRESHNESS_SOURCE = "real_estate_reaction_snapshots";

    private final RealEstateReactionSnapshotRepository snapshotRepository;
    private final RealEstateTargetRepository targetRepository;
    private final RealEstateTargetGraphService targetGraphService;
    private final RealEstateTimelineService timelineService;

    public RealEstateReactionSnapshotService(
            RealEstateReactionSnapshotRepository snapshotRepository,
            RealEstateTargetRepository targetRepository,
            RealEstateTargetGraphService targetGraphService,
            RealEstateTimelineService timelineService
    ) {
        this.snapshotRepository = snapshotRepository;
        this.targetRepository = targetRepository;
        this.targetGraphService = targetGraphService;
        this.timelineService = timelineService;
    }

    @Transactional
    public int upsertAll(Collection<RealEstateReactionSnapshotRequest> requests) {
        Instant now = Instant.now();
        int accepted = 0;
        for (RealEstateReactionSnapshotRequest request : requests) {
            RealEstateTarget target = targetRepository.findById(request.targetId())
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.BAD_REQUEST,
                            "unknown real-estate target: " + request.targetId()
                    ));
            String targetType = normalizeLower(request.targetType());
            RealEstateReactionSnapshot snapshot = snapshotRepository
                    .findByTargetIdAndWindowStartAndWindowEnd(target.getId(), request.windowStart(), request.windowEnd())
                    .orElseGet(() -> new RealEstateReactionSnapshot(target, request.windowStart(), request.windowEnd()));
            snapshot.update(
                    targetType,
                    target,
                    request.asOf(),
                    request.mentionCount(),
                    request.previousMentionCount(),
                    request.expectationScore(),
                    request.concernScore(),
                    request.neutralScore(),
                    request.heatScore(),
                    request.confidence(),
                    request.sourceCount(),
                    request.sourceSkew(),
                    normalizeLower(request.coverageStatus()),
                    request.stale(),
                    issueEntities(request.issues()),
                    now
            );
            snapshotRepository.save(snapshot);
            materializeTimelineEvent(snapshot, now);
            accepted++;
        }
        return accepted;
    }

    @Transactional(readOnly = true)
    public RealEstateReactionRankingResponse ranking(
            String targetType,
            Instant windowStart,
            int windowMinutes,
            int limit
    ) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        Instant windowEnd = windowStart.plus(Duration.ofMinutes(windowMinutes));
        List<RealEstateReactionSnapshot> snapshots = snapshotRepository.findRanking(
                normalizeLower(targetType),
                windowStart,
                windowEnd,
                PageRequest.of(0, boundedLimit)
        );
        List<RealEstateReactionRankingRowResponse> rows = toRankingRows(snapshots);
        return new RealEstateReactionRankingResponse(
                windowMinutes + "m",
                windowStart,
                windowEnd,
                freshness(snapshots),
                rows
        );
    }

    @Transactional(readOnly = true)
    public RealEstateReactionRankingResponse latestRanking(
            String targetType,
            int windowMinutes,
            int limit
    ) {
        String normalizedTargetType = normalizeLower(targetType);
        Instant latestWindowStart = snapshotRepository.findLatestWindowStart(normalizedTargetType);
        if (latestWindowStart == null) {
            return new RealEstateReactionRankingResponse(
                    windowMinutes + "m",
                    null,
                    null,
                    freshness(List.of()),
                    List.of()
            );
        }
        return ranking(normalizedTargetType, latestWindowStart, windowMinutes, limit);
    }

    @Transactional(readOnly = true)
    public RealEstateReactionSnapshotDetailResponse targetSnapshot(
            String targetId,
            Instant windowStart,
            int windowMinutes
    ) {
        RealEstateTarget target = targetRepository.findById(targetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        Instant effectiveWindowStart = windowStart == null
                ? snapshotRepository.findLatestWindowStartByTargetId(targetId)
                : windowStart;
        if (effectiveWindowStart == null) {
            return emptyTargetSnapshot(target, windowMinutes);
        }
        Instant windowEnd = effectiveWindowStart.plus(Duration.ofMinutes(windowMinutes));
        return snapshotRepository.findTargetSnapshot(targetId, effectiveWindowStart, windowEnd)
                .map(snapshot -> toDetail(snapshot, windowMinutes))
                .orElseGet(() -> emptyTargetSnapshot(target, windowMinutes, effectiveWindowStart, windowEnd));
    }

    @Transactional(readOnly = true)
    public RealEstateReactionGraphResponse targetReactionGraph(
            String targetId,
            String direction,
            String edgeType,
            Instant windowStart,
            int windowMinutes,
            int limit
    ) {
        targetRepository.findById(targetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        String normalizedDirection = normalizeDirection(direction);
        String normalizedEdgeType = normalizeNullable(edgeType);
        List<RealEstateTargetEdgeResponse> edges = targetGraphService.publicGraph(
                targetId,
                normalizedDirection,
                normalizedEdgeType,
                limit
        );
        Instant effectiveWindowStart = windowStart == null
                ? latestWindowStartForGraph(targetId, normalizedDirection, edges)
                : windowStart;
        Instant windowEnd = effectiveWindowStart == null
                ? null
                : effectiveWindowStart.plus(Duration.ofMinutes(windowMinutes));
        List<RealEstateReactionGraphItemResponse> items = edges.stream()
                .map(edge -> {
                    RealEstateReactionGraphTargetResponse relatedTarget = relatedTarget(targetId, normalizedDirection, edge);
                    return new RealEstateReactionGraphItemResponse(
                            edge,
                            relatedTarget,
                            targetSnapshot(relatedTarget.targetId(), effectiveWindowStart, windowMinutes)
                    );
                })
                .toList();
        return new RealEstateReactionGraphResponse(
                targetId,
                normalizedDirection,
                normalizedEdgeType,
                windowMinutes + "m",
                effectiveWindowStart,
                windowEnd,
                items
        );
    }

    private List<RealEstateReactionRankingRowResponse> toRankingRows(List<RealEstateReactionSnapshot> snapshots) {
        int[] rank = {1};
        return snapshots.stream()
                .map(snapshot -> new RealEstateReactionRankingRowResponse(
                        rank[0]++,
                        snapshot.getTarget().getId(),
                        snapshot.getTargetType(),
                        snapshot.getTarget().getDisplayName(),
                        snapshot.getMentionCount(),
                        mentionDeltaPct(snapshot),
                        ratio(snapshot),
                        snapshot.getHeatScore(),
                        round(snapshot.getConfidence(), 2),
                        snapshot.getSourceCount(),
                        round(snapshot.getSourceSkew(), 2),
                snapshot.getCoverageStatus(),
                snapshot.isStale(),
                issueResponses(snapshot)
        ))
                .toList();
    }

    private RealEstateReactionSnapshotDetailResponse toDetail(
            RealEstateReactionSnapshot snapshot,
            int windowMinutes
    ) {
        return new RealEstateReactionSnapshotDetailResponse(
                snapshot.getTarget().getId(),
                snapshot.getTargetType(),
                snapshot.getTarget().getDisplayName(),
                windowMinutes + "m",
                snapshot.getWindowStart(),
                snapshot.getWindowEnd(),
                snapshot.getMentionCount(),
                snapshot.getPreviousMentionCount(),
                mentionDeltaPct(snapshot),
                dominantDirection(snapshot),
                ratio(snapshot),
                snapshot.getHeatScore(),
                new RealEstateReactionQualityResponse(
                        round(snapshot.getConfidence(), 2),
                        snapshot.getSourceCount(),
                        round(snapshot.getSourceSkew(), 2),
                        snapshot.getCoverageStatus(),
                        snapshot.isStale()
                ),
                freshness(List.of(snapshot)),
                issueResponses(snapshot)
        );
    }

    private RealEstateReactionSnapshotDetailResponse emptyTargetSnapshot(
            RealEstateTarget target,
            int windowMinutes
    ) {
        return emptyTargetSnapshot(target, windowMinutes, null, null);
    }

    private RealEstateReactionSnapshotDetailResponse emptyTargetSnapshot(
            RealEstateTarget target,
            int windowMinutes,
            Instant windowStart,
            Instant windowEnd
    ) {
        return new RealEstateReactionSnapshotDetailResponse(
                target.getId(),
                target.getTargetType(),
                target.getDisplayName(),
                windowMinutes + "m",
                windowStart,
                windowEnd,
                0,
                0,
                0.0,
                "neutral",
                new RealEstateReactionRatioResponse(0.0, 0.0, 0.0),
                0,
                new RealEstateReactionQualityResponse(0.0, 0, 0.0, "empty", true),
                freshness(List.of()),
                List.of()
        );
    }

    private Instant latestWindowStartForGraph(
            String targetId,
            String direction,
            List<RealEstateTargetEdgeResponse> edges
    ) {
        Set<String> targetIds = new LinkedHashSet<>();
        targetIds.add(targetId);
        edges.stream()
                .map(edge -> relatedTarget(targetId, direction, edge).targetId())
                .forEach(targetIds::add);
        return snapshotRepository.findLatestWindowStartByTargetIds(targetIds);
    }

    private RealEstateReactionGraphTargetResponse relatedTarget(
            String targetId,
            String direction,
            RealEstateTargetEdgeResponse edge
    ) {
        if ("in".equals(direction)) {
            return new RealEstateReactionGraphTargetResponse(
                    edge.fromTargetId(),
                    edge.fromTargetType(),
                    edge.fromDisplayName(),
                    edge.fromSlug()
            );
        }
        if ("out".equals(direction)) {
            return new RealEstateReactionGraphTargetResponse(
                    edge.toTargetId(),
                    edge.toTargetType(),
                    edge.toDisplayName(),
                    edge.toSlug()
            );
        }
        if (targetId.equals(edge.fromTargetId())) {
            return new RealEstateReactionGraphTargetResponse(
                    edge.toTargetId(),
                    edge.toTargetType(),
                    edge.toDisplayName(),
                    edge.toSlug()
            );
        }
        return new RealEstateReactionGraphTargetResponse(
                edge.fromTargetId(),
                edge.fromTargetType(),
                edge.fromDisplayName(),
                edge.fromSlug()
        );
    }

    private RealEstateReactionRankingFreshnessResponse freshness(List<RealEstateReactionSnapshot> snapshots) {
        Instant asOf = snapshots.stream()
                .map(RealEstateReactionSnapshot::getAsOf)
                .filter(Objects::nonNull)
                .max(Instant::compareTo)
                .orElse(null);
        int staleCount = (int) snapshots.stream().filter(RealEstateReactionSnapshot::isStale).count();
        int sourceCount = snapshots.stream()
                .mapToInt(RealEstateReactionSnapshot::getSourceCount)
                .max()
                .orElse(0);
        String coverageStatus = staleCount > 0
                ? "partial"
                : snapshots.stream().allMatch(snapshot -> "complete".equals(snapshot.getCoverageStatus()))
                ? "complete"
                : snapshots.isEmpty() ? "empty" : "partial";
        return new RealEstateReactionRankingFreshnessResponse(
                FRESHNESS_SOURCE,
                asOf,
                staleCount,
                sourceCount,
                coverageStatus
        );
    }

    private RealEstateReactionRatioResponse ratio(RealEstateReactionSnapshot snapshot) {
        double total = snapshot.getExpectationScore() + snapshot.getConcernScore() + snapshot.getNeutralScore();
        if (total <= 0) {
            return new RealEstateReactionRatioResponse(0.0, 0.0, 0.0);
        }
        return new RealEstateReactionRatioResponse(
                round(snapshot.getExpectationScore() / total, 2),
                round(snapshot.getConcernScore() / total, 2),
                round(snapshot.getNeutralScore() / total, 2)
        );
    }

    private String dominantDirection(RealEstateReactionSnapshot snapshot) {
        double expectation = snapshot.getExpectationScore();
        double concern = snapshot.getConcernScore();
        double neutral = snapshot.getNeutralScore();
        if (expectation >= concern && expectation >= neutral) {
            return "expectation";
        }
        if (concern >= expectation && concern >= neutral) {
            return "concern";
        }
        return "neutral";
    }

    private List<RealEstateReactionSnapshotIssueResponse> issueResponses(RealEstateReactionSnapshot snapshot) {
        return snapshot.getIssues().stream()
                .sorted(Comparator
                        .comparingDouble(RealEstateReactionSnapshotIssue::getShare).reversed()
                        .thenComparing(RealEstateReactionSnapshotIssue::getLabel))
                .map(issue -> new RealEstateReactionSnapshotIssueResponse(
                        issue.getIssueKey(),
                        issue.getLabel(),
                        round(issue.getShare(), 2),
                        issue.getDirection(),
                        issue.getSummary(),
                        round(issue.getConfidence(), 2)
                ))
                .toList();
    }

    private double mentionDeltaPct(RealEstateReactionSnapshot snapshot) {
        if (snapshot.getPreviousMentionCount() <= 0) {
            return snapshot.getMentionCount() > 0 ? 100.0 : 0.0;
        }
        double delta = (snapshot.getMentionCount() - snapshot.getPreviousMentionCount())
                * 100.0
                / snapshot.getPreviousMentionCount();
        return round(delta, 1);
    }

    private void materializeTimelineEvent(RealEstateReactionSnapshot snapshot, Instant now) {
        if (snapshot.getId() == null) {
            return;
        }
        String dominantDirection = dominantDirection(snapshot);
        timelineService.upsertSourceTimeline(
                snapshot.getTarget().getId(),
                "reaction",
                "reaction_snapshot",
                String.valueOf(snapshot.getId()),
                "커뮤니티 " + directionLabel(dominantDirection) + " 우세",
                reactionTimelineSummary(snapshot, dominantDirection),
                snapshot.getWindowEnd(),
                snapshot.getAsOf(),
                snapshotDataStatus(snapshot),
                now
        );
    }

    private String reactionTimelineSummary(RealEstateReactionSnapshot snapshot, String dominantDirection) {
        List<String> parts = new ArrayList<>();
        parts.add("언급 " + snapshot.getMentionCount() + "건");
        parts.add("전 구간 대비 " + formatSignedPercent(mentionDeltaPct(snapshot)));
        parts.add(directionLabel(dominantDirection) + " 우세");
        String issueLabels = snapshot.getIssues().stream()
                .sorted(Comparator
                        .comparingDouble(RealEstateReactionSnapshotIssue::getShare).reversed()
                        .thenComparing(RealEstateReactionSnapshotIssue::getLabel))
                .map(RealEstateReactionSnapshotIssue::getLabel)
                .limit(3)
                .reduce((left, right) -> left + ", " + right)
                .orElse(null);
        if (issueLabels != null) {
            parts.add("주요 쟁점 " + issueLabels);
        }
        return String.join(" · ", parts);
    }

    private String snapshotDataStatus(RealEstateReactionSnapshot snapshot) {
        if (snapshot.isStale()) {
            return "stale";
        }
        return "complete".equals(snapshot.getCoverageStatus()) ? "ok" : "partial";
    }

    private static String directionLabel(String direction) {
        return switch (direction) {
            case "expectation" -> "기대";
            case "concern" -> "우려";
            default -> "중립";
        };
    }

    private static String formatSignedPercent(double value) {
        return String.format(Locale.KOREA, "%+.1f%%", value);
    }

    private List<RealEstateReactionSnapshotIssue> issueEntities(List<RealEstateReactionSnapshotIssueRequest> requests) {
        if (requests == null) {
            return List.of();
        }
        return requests.stream()
                .map(request -> new RealEstateReactionSnapshotIssue(
                        normalizeLower(request.issueKey()),
                        request.label().trim(),
                        request.share(),
                        normalizeLower(request.direction()),
                        trimToNull(request.summary()),
                        request.confidence()
                ))
                .toList();
    }

    private static String normalizeLower(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private static String normalizeDirection(String value) {
        String normalized = normalizeNullable(value);
        if ("in".equals(normalized) || "out".equals(normalized) || "both".equals(normalized)) {
            return normalized;
        }
        return "both";
    }

    private static String normalizeNullable(String value) {
        String trimmed = trimToNull(value);
        return trimmed == null ? null : normalizeLower(trimmed);
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static double round(double value, int places) {
        double factor = Math.pow(10, places);
        return Math.round(value * factor) / factor;
    }
}
