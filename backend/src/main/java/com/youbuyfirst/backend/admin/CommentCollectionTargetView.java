package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.post.CommunityCommentCollectionTarget;
import com.youbuyfirst.backend.post.CommunityPost;

import java.time.Instant;

public record CommentCollectionTargetView(
        Long id,
        Long postId,
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
        Instant createdAt
) {
    public static CommentCollectionTargetView from(CommunityCommentCollectionTarget target) {
        CommunityPost post = target.getPost();
        return new CommentCollectionTargetView(
                target.getId(),
                post == null ? null : post.getId(),
                target.getSource(),
                target.getExternalId(),
                target.getBoardId(),
                target.getTriggerReason(),
                target.getTriggeredAt(),
                target.getMaxComments(),
                target.getPriority(),
                target.getViewCount(),
                target.getRecommendCount(),
                target.getCommentCount(),
                target.getStatus(),
                target.getCrawlRunId(),
                target.getCreatedAt()
        );
    }
}
