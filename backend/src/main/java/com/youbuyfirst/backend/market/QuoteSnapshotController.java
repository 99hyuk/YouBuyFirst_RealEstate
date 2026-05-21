package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.QuoteSnapshotBatchRequest;
import com.youbuyfirst.backend.market.dto.QuoteSnapshotResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class QuoteSnapshotController {

    private final QuoteSnapshotService quoteSnapshotService;

    public QuoteSnapshotController(QuoteSnapshotService quoteSnapshotService) {
        this.quoteSnapshotService = quoteSnapshotService;
    }

    @PostMapping("/internal/market/quote-snapshots")
    public ResponseEntity<Void> upsert(@Valid @RequestBody QuoteSnapshotBatchRequest request) {
        quoteSnapshotService.upsertAll(request.items());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/api/quotes")
    public List<QuoteSnapshotResponse> quotes(@RequestParam(required = false) String symbols) {
        return quoteSnapshotService.list(symbols);
    }
}
