package com.humanindicator.backend.ingestion;

import com.humanindicator.backend.ingestion.dto.CrawlRunReportRequest;
import com.humanindicator.backend.ingestion.dto.IngestionRequest;
import com.humanindicator.backend.ingestion.dto.IngestionResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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

    @PostMapping("/crawl-runs")
    public void recordCrawlRun(@Valid @RequestBody CrawlRunReportRequest request) {
        ingestionService.recordCrawlRun(request);
    }
}
