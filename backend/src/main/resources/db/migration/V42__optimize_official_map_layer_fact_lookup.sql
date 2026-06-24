CREATE INDEX idx_remf_official_target_dataset_observed_object
    ON real_estate_market_facts (
        target_id,
        fact_type,
        provider_dataset,
        observed_at DESC,
        provider_object_id
    );

CREATE INDEX idx_remf_official_legal_dataset_observed_object
    ON real_estate_market_facts (
        legal_dong_code,
        fact_type,
        provider_dataset,
        observed_at DESC,
        provider_object_id
    );
