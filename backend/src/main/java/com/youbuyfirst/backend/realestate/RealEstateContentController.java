package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateContentBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentListResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateContentController {

    private final RealEstateContentService service;

    public RealEstateContentController(RealEstateContentService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/content-items")
    public RealEstateContentBatchResponse upsertContentItems(
            @Valid @RequestBody RealEstateContentBatchRequest request
    ) {
        return service.upsertAll(request.items());
    }

    @GetMapping("/api/realestate/targets/{targetId}/content")
    public RealEstateContentListResponse targetContent(
            @PathVariable String targetId,
            @RequestParam(defaultValue = "all") String feed,
            @RequestParam(defaultValue = "50") int limit
    ) {
        return new RealEstateContentListResponse(service.listForTarget(targetId, feed, limit));
    }

    @GetMapping("/api/realestate/newsroom")
    public RealEstateContentListResponse newsroom(
            @RequestParam(defaultValue = "all") String feed,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "15") int pageSize
    ) {
        return new RealEstateContentListResponse(service.listNewsroom(feed, page, pageSize));
    }
}
