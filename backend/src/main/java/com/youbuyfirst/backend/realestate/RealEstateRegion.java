package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "real_estate_regions")
public class RealEstateRegion {

    @Id
    @Column(name = "target_id", length = 120)
    private String targetId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "region_level", nullable = false, length = 30)
    private String regionLevel;

    @Column(name = "parent_region_id", length = 120)
    private String parentRegionId;

    @Column(name = "legal_dong_code", length = 20)
    private String legalDongCode;

    @Column(name = "region_code", length = 30)
    private String regionCode;

    @Column(nullable = false, length = 120)
    private String source;

    protected RealEstateRegion() {
    }

    public RealEstateRegion(
            String targetId,
            String regionLevel,
            String parentRegionId,
            String legalDongCode,
            String regionCode,
            String source
    ) {
        this.targetId = targetId;
        update(regionLevel, parentRegionId, legalDongCode, regionCode, source);
    }

    public void update(
            String regionLevel,
            String parentRegionId,
            String legalDongCode,
            String regionCode,
            String source
    ) {
        this.regionLevel = regionLevel;
        this.parentRegionId = parentRegionId;
        this.legalDongCode = legalDongCode;
        this.regionCode = regionCode;
        this.source = source;
    }

    public String getTargetId() {
        return targetId;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public String getRegionLevel() {
        return regionLevel;
    }

    public String getParentRegionId() {
        return parentRegionId;
    }

    public String getLegalDongCode() {
        return legalDongCode;
    }

    public String getRegionCode() {
        return regionCode;
    }

    public String getSource() {
        return source;
    }
}
