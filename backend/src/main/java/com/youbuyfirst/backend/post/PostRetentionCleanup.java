package com.youbuyfirst.backend.post;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;

@Component
public class PostRetentionCleanup {

    private final CommunityPostRepository postRepository;
    private final int retentionDays;

    public PostRetentionCleanup(CommunityPostRepository postRepository, @Value("${app.retention.post-days:30}") int retentionDays) {
        this.postRepository = postRepository;
        this.retentionDays = retentionDays;
    }

    @Transactional
    @Scheduled(cron = "${app.retention.cleanup-cron:0 15 3 * * *}", zone = "UTC")
    public void cleanupExpiredPosts() {
        Instant cutoff = Instant.now().minus(Duration.ofDays(retentionDays));
        postRepository.deleteByPublishedAtBefore(cutoff);
    }
}
