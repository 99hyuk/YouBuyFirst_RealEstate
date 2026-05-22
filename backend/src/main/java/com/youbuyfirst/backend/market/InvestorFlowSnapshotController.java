package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.InvestorFlowBatchRequest;
import com.youbuyfirst.backend.market.dto.InvestorFlowSnapshotResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
public class InvestorFlowSnapshotController {

    private final InvestorFlowSnapshotService investorFlowSnapshotService;

    public InvestorFlowSnapshotController(InvestorFlowSnapshotService investorFlowSnapshotService) {
        this.investorFlowSnapshotService = investorFlowSnapshotService;
    }

    @PostMapping("/internal/market/investor-flows")
    public ResponseEntity<Void> upsert(@Valid @RequestBody InvestorFlowBatchRequest request) {
        investorFlowSnapshotService.upsertAll(request.items());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/api/market/investor-flows/history")
    public List<InvestorFlowSnapshotResponse> investorFlowHistory(
            @RequestParam String symbol,
            @RequestParam(defaultValue = "20") int limit
    ) {
        if (symbol == null || symbol.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "symbol is required");
        }
        return investorFlowSnapshotService.history(symbol, limit);
    }
}
