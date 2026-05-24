package com.youbuyfirst.backend.post;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "community_comment_collection_targets",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_comment_target_source_external",
                columnNames = {"source", "external_id"}
        )
)
public class CommunityCommentCollectionTarget {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "post_id")
    private CommunityPost post;

    @Column(nullable = false, length = 40)
    private String source;

    @Column(name = "external_id", nullable = false, length = 200)
    private String externalId;

    @Column(name = "board_id", length = 120)
    private String boardId;

    @Column(name = "trigger_reason", nullable = false, length = 40)
    private String triggerReason;

    @Column(name = "triggered_at", nullable = false)
    private Instant triggeredAt;

    @Column(name = "max_comments", nullable = false)
    private Integer maxComments;

    @Column(nullable = false)
    private Integer priority;

    @Column(name = "view_count")
    private Integer viewCount;

    @Column(name = "recommend_count")
    private Integer recommendCount;

    @Column(name = "comment_count")
    private Integer commentCount;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(name = "crawl_run_id", length = 160)
    private String crawlRunId;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected CommunityCommentCollectionTarget() {
    }

    public CommunityCommentCollectionTarget(
            CommunityPost post,
            String source,
            String externalId,
            String boardId,
            String triggerReason,
            Instant triggeredAt,
            Integer maxComments,
            Integer priority,
            Integer viewCount,
            Integer recommendCount,
            Integer commentCount,
            String status,
            String crawlRunId,
            Instant createdAt,
            Instant updatedAt
    ) {
        this.post = post;
        this.source = source;
        this.externalId = externalId;
        this.boardId = boardId;
        this.triggerReason = triggerReason;
        this.triggeredAt = triggeredAt;
        this.maxComments = maxComments;
        this.priority = priority;
        this.viewCount = viewCount;
        this.recommendCount = recommendCount;
        this.commentCount = commentCount;
        this.status = status;
        this.crawlRunId = crawlRunId;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public void refreshFrom(
            CommunityPost post,
            String boardId,
            String triggerReason,
            Instant triggeredAt,
            Integer maxComments,
            Integer priority,
            Integer viewCount,
            Integer recommendCount,
            Integer commentCount,
            String crawlRunId,
            Instant updatedAt
    ) {
        if (this.post == null && post != null) {
            this.post = post;
        }
        if (boardId != null) {
            this.boardId = boardId;
        }
        if (priority < this.priority || (priority.equals(this.priority) && triggeredAt.isAfter(this.triggeredAt))) {
            this.triggerReason = triggerReason;
            this.triggeredAt = triggeredAt;
        }
        this.maxComments = Math.max(this.maxComments, maxComments);
        this.priority = Math.min(this.priority, priority);
        if (viewCount != null) {
            this.viewCount = viewCount;
        }
        if (recommendCount != null) {
            this.recommendCount = recommendCount;
        }
        if (commentCount != null) {
            this.commentCount = commentCount;
        }
        this.crawlRunId = crawlRunId;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public CommunityPost getPost() {
        return post;
    }

    public String getSource() {
        return source;
    }

    public String getExternalId() {
        return externalId;
    }

    public String getBoardId() {
        return boardId;
    }

    public String getTriggerReason() {
        return triggerReason;
    }

    public Instant getTriggeredAt() {
        return triggeredAt;
    }

    public Integer getMaxComments() {
        return maxComments;
    }

    public Integer getPriority() {
        return priority;
    }

    public Integer getViewCount() {
        return viewCount;
    }

    public Integer getRecommendCount() {
        return recommendCount;
    }

    public Integer getCommentCount() {
        return commentCount;
    }

    public String getStatus() {
        return status;
    }

    public String getCrawlRunId() {
        return crawlRunId;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
