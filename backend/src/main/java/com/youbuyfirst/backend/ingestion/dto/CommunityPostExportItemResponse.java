package com.youbuyfirst.backend.ingestion.dto;

import com.youbuyfirst.backend.post.CommunityPost;

import java.time.Instant;

public record CommunityPostExportItemResponse(
        String source,
        String externalId,
        String url,
        String title,
        String contentSnippet,
        String boardId,
        Integer viewCount,
        Integer recommendCount,
        Integer commentCount,
        Instant publishedAt
) {
    public static CommunityPostExportItemResponse from(CommunityPost post) {
        return new CommunityPostExportItemResponse(
                post.getSource(),
                post.getExternalId(),
                post.getUrl(),
                post.getTitle(),
                post.getContentSnippet(),
                post.getBoardId(),
                post.getViewCount(),
                post.getRecommendCount(),
                post.getCommentCount(),
                post.getPublishedAt()
        );
    }
}
