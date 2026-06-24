package com.youbuyfirst.backend.realestate.batch;

import java.util.Map;

public interface RealEstateExternalFetchClient {
    RealEstateExternalFetchResult fetch(String url);

    RealEstateExternalFetchResult postForm(String url, Map<String, String> form, Map<String, String> headers);
}
