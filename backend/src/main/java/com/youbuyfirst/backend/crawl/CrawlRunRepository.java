package com.youbuyfirst.backend.crawl;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CrawlRunRepository extends JpaRepository<CrawlRun, Long> {

    List<CrawlRun> findByOrderByStartedAtDesc(Pageable pageable);
}

