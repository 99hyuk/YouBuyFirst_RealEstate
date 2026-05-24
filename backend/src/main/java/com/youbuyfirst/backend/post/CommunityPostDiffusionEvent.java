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
        name = "community_post_diffusion_events",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_post_diffusion_source_external_type_observed",
                columnNames = {"source", "external_id", "diffusion_type", "observed_at"}
        )
)
public class CommunityPostDiffusionEvent {

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

    @Column(name = "diffusion_type", nullable = false, length = 40)
    private String diffusionType;

    @Column(name = "list_position")
    private Integer listPosition;

    @Column(name = "observed_at", nullable = false)
    private Instant observedAt;

    @Column(name = "view_count")
    private Integer viewCount;

    @Column(name = "recommend_count")
    private Integer recommendCount;

    @Column(name = "comment_count")
    private Integer commentCount;

    @Column(name = "diffusion_only", nullable = false)
    private boolean diffusionOnly;

    @Column(name = "crawl_run_id", length = 160)
    private String crawlRunId;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected CommunityPostDiffusionEvent() {
    }

    public CommunityPostDiffusionEvent(
            CommunityPost post,
            String source,
            String externalId,
            String boardId,
            String diffusionType,
            Integer listPosition,
            Instant observedAt,
            Integer viewCount,
            Integer recommendCount,
            Integer commentCount,
            boolean diffusionOnly,
            String crawlRunId,
            Instant createdAt
    ) {
        this.post = post;
        this.source = source;
        this.externalId = externalId;
        this.boardId = boardId;
        this.diffusionType = diffusionType;
        this.listPosition = listPosition;
        this.observedAt = observedAt;
        this.viewCount = viewCount;
        this.recommendCount = recommendCount;
        this.commentCount = commentCount;
        this.diffusionOnly = diffusionOnly;
        this.crawlRunId = crawlRunId;
        this.createdAt = createdAt;
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

    public String getDiffusionType() {
        return diffusionType;
    }

    public Integer getListPosition() {
        return listPosition;
    }

    public Instant getObservedAt() {
        return observedAt;
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

    public boolean isDiffusionOnly() {
        return diffusionOnly;
    }

    public String getCrawlRunId() {
        return crawlRunId;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
