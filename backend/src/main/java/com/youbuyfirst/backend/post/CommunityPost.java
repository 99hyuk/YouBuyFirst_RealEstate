package com.youbuyfirst.backend.post;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "community_posts",
        uniqueConstraints = @UniqueConstraint(name = "uk_post_source_external", columnNames = {"source", "external_id"})
)
public class CommunityPost {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String source;

    @Column(name = "external_id", nullable = false, length = 200)
    private String externalId;

    @Column(nullable = false, length = 1000)
    private String url;

    @Column(nullable = false, length = 500)
    private String title;

    @Column(name = "content_snippet", length = 1000)
    private String contentSnippet;

    @Column(name = "board_id", length = 120)
    private String boardId;

    @Column(name = "view_count")
    private Integer viewCount;

    @Column(name = "recommend_count")
    private Integer recommendCount;

    @Column(name = "comment_count")
    private Integer commentCount;

    @Column(name = "author_hash", nullable = false, length = 64)
    private String authorHash;

    @Column(name = "published_at", nullable = false)
    private Instant publishedAt;

    @Column(name = "content_hash", nullable = false, length = 64)
    private String contentHash;

    @Column(name = "crawled_at", nullable = false)
    private Instant crawledAt;

    protected CommunityPost() {
    }

    public CommunityPost(String source, String externalId, String url, String title, String contentSnippet, String authorHash, Instant publishedAt, String contentHash, Instant crawledAt) {
        this(source, externalId, url, title, contentSnippet, null, null, null, null, authorHash, publishedAt, contentHash, crawledAt);
    }

    public CommunityPost(
            String source,
            String externalId,
            String url,
            String title,
            String contentSnippet,
            String boardId,
            Integer viewCount,
            Integer recommendCount,
            Integer commentCount,
            String authorHash,
            Instant publishedAt,
            String contentHash,
            Instant crawledAt
    ) {
        this.source = source;
        this.externalId = externalId;
        this.url = url;
        this.title = title;
        this.contentSnippet = contentSnippet;
        this.boardId = boardId;
        this.viewCount = viewCount;
        this.recommendCount = recommendCount;
        this.commentCount = commentCount;
        this.authorHash = authorHash;
        this.publishedAt = publishedAt;
        this.contentHash = contentHash;
        this.crawledAt = crawledAt;
    }

    public Long getId() {
        return id;
    }

    public String getSource() {
        return source;
    }

    public String getExternalId() {
        return externalId;
    }

    public String getUrl() {
        return url;
    }

    public String getTitle() {
        return title;
    }

    public String getContentSnippet() {
        return contentSnippet;
    }

    public String getBoardId() {
        return boardId;
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

    public String getAuthorHash() {
        return authorHash;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public String getContentHash() {
        return contentHash;
    }

    public Instant getCrawledAt() {
        return crawledAt;
    }
}
