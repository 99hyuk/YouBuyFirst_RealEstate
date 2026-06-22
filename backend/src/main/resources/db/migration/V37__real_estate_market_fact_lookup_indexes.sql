CREATE INDEX idx_remf_observed_provider_object
    ON real_estate_market_facts (observed_at DESC, provider_object_id ASC);

CREATE INDEX idx_remf_fact_observed_provider_object
    ON real_estate_market_facts (fact_type, observed_at DESC, provider_object_id ASC);

CREATE INDEX idx_remf_legal_fact_observed_provider_object
    ON real_estate_market_facts (legal_dong_code, fact_type, observed_at DESC, provider_object_id ASC);

CREATE INDEX idx_remf_target_fact_observed_provider_object
    ON real_estate_market_facts (target_id, fact_type, observed_at DESC, provider_object_id ASC);
