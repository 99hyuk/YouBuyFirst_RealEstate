package com.youbuyfirst.backend.crawl;

import com.youbuyfirst.backend.crawl.dto.CrawlTargetClaimRequest;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetClaimResponse;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetCompletionRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/crawl-targets")
public class CrawlTargetController {

    private final CrawlTargetService crawlTargetService;

    public CrawlTargetController(CrawlTargetService crawlTargetService) {
        this.crawlTargetService = crawlTargetService;
    }

    @PostMapping("/claim")
    public CrawlTargetClaimResponse claim(@Valid @RequestBody CrawlTargetClaimRequest request) {
        return crawlTargetService.claim(request);
    }

    @PostMapping("/{targetId}/complete")
    public ResponseEntity<Void> complete(@PathVariable String targetId, @Valid @RequestBody CrawlTargetCompletionRequest request) {
        crawlTargetService.complete(targetId, request);
        return ResponseEntity.ok().build();
    }
}
