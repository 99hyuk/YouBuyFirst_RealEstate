package com.youbuyfirst.backend.crawl;

public enum CrawlTargetKind {
    COMMUNITY_BOARD("community-board");

    private final String value;

    CrawlTargetKind(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }
}
