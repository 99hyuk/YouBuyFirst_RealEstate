package com.youbuyfirst.backend.crawl;

public enum CrawlTargetKind {
    STOCK_BOARD("stock-board"),
    COMMUNITY_BOARD("community-board");

    private final String value;

    CrawlTargetKind(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }
}
