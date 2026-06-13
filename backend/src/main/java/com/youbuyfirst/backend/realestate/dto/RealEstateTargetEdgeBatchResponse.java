package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetEdgeBatchResponse(
        int acceptedEdges,
        int createdEdges,
        int updatedEdges,
        int skippedEdges
) {
}
