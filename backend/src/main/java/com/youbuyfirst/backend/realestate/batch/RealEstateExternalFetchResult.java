package com.youbuyfirst.backend.realestate.batch;

public record RealEstateExternalFetchResult(
        boolean success,
        int statusCode,
        String body,
        String errorMessage
) {
    public static RealEstateExternalFetchResult ok(String body) {
        return new RealEstateExternalFetchResult(true, 200, body, null);
    }

    public static RealEstateExternalFetchResult failed(int statusCode, String errorMessage) {
        return new RealEstateExternalFetchResult(false, statusCode, null, errorMessage);
    }
}
