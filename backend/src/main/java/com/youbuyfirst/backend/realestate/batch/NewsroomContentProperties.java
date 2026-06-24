package com.youbuyfirst.backend.realestate.batch;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

@ConfigurationProperties(prefix = "app.realestate.newsroom")
public class NewsroomContentProperties {

    private List<Source> sources = new ArrayList<>();

    public List<Source> getSources() {
        return sources;
    }

    public void setSources(List<Source> sources) {
        this.sources = sources == null ? new ArrayList<>() : sources;
    }

    public static class Source {
        private String id;
        private String feed;
        private String sourceId;
        private String url;
        private String statusLabel;
        private String dataStatus;
        private List<String> requiredTerms = new ArrayList<>();
        private List<String> requiredTopicTerms = new ArrayList<>();
        private List<String> excludedTerms = new ArrayList<>();
        private List<String> allowedDomains = new ArrayList<>();
        private Integer maxItems;
        private Integer maxAgeDays;
        private Integer minDurationSeconds;
        private Long minViewCount;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getFeed() {
            return feed;
        }

        public void setFeed(String feed) {
            this.feed = feed;
        }

        public String getSourceId() {
            return sourceId;
        }

        public void setSourceId(String sourceId) {
            this.sourceId = sourceId;
        }

        public String getUrl() {
            return url;
        }

        public void setUrl(String url) {
            this.url = url;
        }

        public String getStatusLabel() {
            return statusLabel;
        }

        public void setStatusLabel(String statusLabel) {
            this.statusLabel = statusLabel;
        }

        public String getDataStatus() {
            return dataStatus;
        }

        public void setDataStatus(String dataStatus) {
            this.dataStatus = dataStatus;
        }

        public List<String> getRequiredTerms() {
            return requiredTerms;
        }

        public void setRequiredTerms(List<String> requiredTerms) {
            this.requiredTerms = requiredTerms == null ? new ArrayList<>() : requiredTerms;
        }

        public List<String> getRequiredTopicTerms() {
            return requiredTopicTerms;
        }

        public void setRequiredTopicTerms(List<String> requiredTopicTerms) {
            this.requiredTopicTerms = requiredTopicTerms == null ? new ArrayList<>() : requiredTopicTerms;
        }

        public List<String> getExcludedTerms() {
            return excludedTerms;
        }

        public void setExcludedTerms(List<String> excludedTerms) {
            this.excludedTerms = excludedTerms == null ? new ArrayList<>() : excludedTerms;
        }

        public List<String> getAllowedDomains() {
            return allowedDomains;
        }

        public void setAllowedDomains(List<String> allowedDomains) {
            this.allowedDomains = allowedDomains == null ? new ArrayList<>() : allowedDomains;
        }

        public Integer getMaxItems() {
            return maxItems;
        }

        public void setMaxItems(Integer maxItems) {
            this.maxItems = maxItems;
        }

        public Integer getMaxAgeDays() {
            return maxAgeDays;
        }

        public void setMaxAgeDays(Integer maxAgeDays) {
            this.maxAgeDays = maxAgeDays;
        }

        public Integer getMinDurationSeconds() {
            return minDurationSeconds;
        }

        public void setMinDurationSeconds(Integer minDurationSeconds) {
            this.minDurationSeconds = minDurationSeconds;
        }

        public Long getMinViewCount() {
            return minViewCount;
        }

        public void setMinViewCount(Long minViewCount) {
            this.minViewCount = minViewCount;
        }
    }
}
