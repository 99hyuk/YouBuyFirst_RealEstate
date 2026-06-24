package com.youbuyfirst.backend.realestate;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "daily_briefings")
public class RealEstateDailyBriefing {

    @Id
    @Column(length = 120)
    private String id;

    @Column(name = "briefing_date", nullable = false)
    private LocalDate briefingDate;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(name = "summary_headlines_json", nullable = false, columnDefinition = "text")
    private String summaryHeadlinesJson;

    @Column(name = "focus_regions_json", nullable = false, columnDefinition = "text")
    private String focusRegionsJson;

    @Column(name = "model_name", length = 80)
    private String modelName;

    @Column(name = "prompt_version", length = 80)
    private String promptVersion;

    @Column(name = "generated_at", nullable = false)
    private Instant generatedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @OrderBy("displayOrder asc, id asc")
    @OneToMany(mappedBy = "briefing", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<RealEstateDailyBriefingSection> sections = new ArrayList<>();

    @OrderBy("displayOrder asc, id asc")
    @OneToMany(mappedBy = "briefing", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<RealEstateDailyBriefingSourceItem> sourceItems = new ArrayList<>();

    protected RealEstateDailyBriefing() {
    }

    public RealEstateDailyBriefing(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            LocalDate briefingDate,
            String title,
            String summaryHeadlinesJson,
            String focusRegionsJson,
            String modelName,
            String promptVersion,
            Instant generatedAt,
            List<RealEstateDailyBriefingSection> nextSections,
            List<RealEstateDailyBriefingSourceItem> nextSourceItems,
            Instant now
    ) {
        this.briefingDate = briefingDate;
        this.title = title;
        this.summaryHeadlinesJson = summaryHeadlinesJson;
        this.focusRegionsJson = focusRegionsJson;
        this.modelName = modelName;
        this.promptVersion = promptVersion;
        this.generatedAt = generatedAt;
        this.sections.clear();
        nextSections.forEach(this::addSection);
        this.sourceItems.clear();
        nextSourceItems.forEach(this::addSourceItem);
        this.updatedAt = now;
    }

    private void addSection(RealEstateDailyBriefingSection section) {
        section.attachTo(this);
        this.sections.add(section);
    }

    private void addSourceItem(RealEstateDailyBriefingSourceItem sourceItem) {
        sourceItem.attachTo(this);
        this.sourceItems.add(sourceItem);
    }

    public String getId() {
        return id;
    }

    public LocalDate getBriefingDate() {
        return briefingDate;
    }

    public String getTitle() {
        return title;
    }

    public String getSummaryHeadlinesJson() {
        return summaryHeadlinesJson;
    }

    public String getFocusRegionsJson() {
        return focusRegionsJson;
    }

    public String getModelName() {
        return modelName;
    }

    public String getPromptVersion() {
        return promptVersion;
    }

    public Instant getGeneratedAt() {
        return generatedAt;
    }

    public List<RealEstateDailyBriefingSection> getSections() {
        return sections;
    }

    public List<RealEstateDailyBriefingSourceItem> getSourceItems() {
        return sourceItems;
    }
}
