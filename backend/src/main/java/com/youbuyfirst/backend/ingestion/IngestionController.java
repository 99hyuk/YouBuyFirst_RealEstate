package com.youbuyfirst.backend.ingestion;

import com.youbuyfirst.backend.ingestion.dto.CommunityPostExportResponse;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionResponse;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

@RestController
@RequestMapping("/internal/ingestions")
public class IngestionController {

    private final IngestionService ingestionService;

    public IngestionController(IngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @PostMapping("/community-posts")
    public IngestionResponse ingestCommunityPosts(@Valid @RequestBody IngestionRequest request) {
        return ingestionService.ingest(request);
    }

    @GetMapping("/community-posts/export")
    public CommunityPostExportResponse exportCommunityPosts(
            @RequestParam(required = false) String source,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant publishedFrom,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant publishedTo,
            @RequestParam(defaultValue = "1000") int limit
    ) {
        return ingestionService.exportCommunityPosts(source, publishedFrom, publishedTo, limit);
    }

    @PostMapping("/crawl-runs")
    public void recordCrawlRun(@Valid @RequestBody CrawlRunReportRequest request) {
        ingestionService.recordCrawlRun(request);
    }
}
