package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.post.CommunityPost;

import java.time.Instant;

public record PostView(
        Long id,
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
    public static PostView from(CommunityPost post) {
        return new PostView(
                post.getId(),
                post.getSource(),
                post.getExternalId(),
                post.getUrl(),
                post.getTitle(),
                post.getContentSnippet(),
                post.getBoardId(),
                post.getViewCount(),
                post.getRecommendCount(),
                post.getCommentCount(),
                post.getAuthorHash(),
                post.getPublishedAt(),
                post.getContentHash(),
                post.getCrawledAt()
        );
    }
}
