package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateAliasBatchRequest(
        List<RealEstateAliasRequest> items
) {
}
