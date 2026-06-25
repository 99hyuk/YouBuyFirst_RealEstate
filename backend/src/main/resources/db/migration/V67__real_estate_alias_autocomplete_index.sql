CREATE INDEX idx_real_estate_aliases_autocomplete_match
    ON real_estate_aliases (review_state, ambiguous, normalized_alias, target_id);
