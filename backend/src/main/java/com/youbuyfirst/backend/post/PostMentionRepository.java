package com.youbuyfirst.backend.post;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.List;

public interface PostMentionRepository extends JpaRepository<PostMention, Long> {

    @Query("""
            select mention
            from PostMention mention
            join fetch mention.instrument instrument
            join fetch mention.post post
            where post.publishedAt >= :from and post.publishedAt < :to
            """)
    List<PostMention> findMentionsInWindow(Instant from, Instant to);
}
