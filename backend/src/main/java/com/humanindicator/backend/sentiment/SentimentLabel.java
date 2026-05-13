package com.humanindicator.backend.sentiment;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum SentimentLabel {
    BULLISH,
    BEARISH,
    NEUTRAL;

    @JsonCreator
    public static SentimentLabel fromJson(String value) {
        return SentimentLabel.valueOf(value.trim().toUpperCase());
    }

    @JsonValue
    public String toJson() {
        return name().toLowerCase();
    }
}

