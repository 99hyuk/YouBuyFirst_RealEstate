package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEvent;

import java.time.Instant;

public record PostDiffusionEventView(
        Long id,
        Long postId,
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
    public static PostDiffusionEventView from(CommunityPostDiffusionEvent event) {
        CommunityPost post = event.getPost();
        return new PostDiffusionEventView(
                event.getId(),
                post == null ? null : post.getId(),
                event.getSource(),
                event.getExternalId(),
                event.getBoardId(),
                event.getDiffusionType(),
                event.getListPosition(),
                event.getObservedAt(),
                event.getViewCount(),
                event.getRecommendCount(),
                event.getCommentCount(),
                event.isDiffusionOnly(),
                event.getCrawlRunId(),
                event.getCreatedAt()
        );
    }
}
