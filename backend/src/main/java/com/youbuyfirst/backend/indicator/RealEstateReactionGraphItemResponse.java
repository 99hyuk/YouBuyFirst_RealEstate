package com.youbuyfirst.backend.indicator;

import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeResponse;

public record RealEstateReactionGraphItemResponse(
        RealEstateTargetEdgeResponse edge,
        RealEstateReactionGraphTargetResponse relatedTarget,
        RealEstateReactionSnapshotDetailResponse reactionSnapshot
) {
}
