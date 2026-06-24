package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "daily_briefing_sections")
public class RealEstateDailyBriefingSection {

    @Id
    @Column(length = 160)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "briefing_id", nullable = false)
    private RealEstateDailyBriefing briefing;

    @Column(name = "section_key", nullable = false, length = 80)
    private String sectionId;

    @Column(nullable = false, length = 120)
    private String title;

    @Column(nullable = false, columnDefinition = "text")
    private String body;

    @Column(name = "display_order", nullable = false)
    private int displayOrder;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateDailyBriefingSection() {
    }

    public RealEstateDailyBriefingSection(
            String id,
            String sectionId,
            String title,
            String body,
            int displayOrder,
            Instant now
    ) {
        this.id = id;
        this.sectionId = sectionId;
        this.title = title;
        this.body = body;
        this.displayOrder = displayOrder;
        this.createdAt = now;
        this.updatedAt = now;
    }

    void attachTo(RealEstateDailyBriefing briefing) {
        this.briefing = briefing;
    }

    public String getId() {
        return id;
    }

    public String getSectionId() {
        return sectionId;
    }

    public String getTitle() {
        return title;
    }

    public String getBody() {
        return body;
    }

    public int getDisplayOrder() {
        return displayOrder;
    }
}
