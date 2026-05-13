package com.humanindicator.backend.sentiment;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.List;

public interface SentimentAnalysisRepository extends JpaRepository<SentimentAnalysis, Long> {

    @Query("""
            select s
            from SentimentAnalysis s
            join fetch s.instrument i
            join fetch s.post p
            where p.publishedAt >= :from and p.publishedAt < :to
            """)
    List<SentimentAnalysis> findAnalysesInWindow(Instant from, Instant to);
}

