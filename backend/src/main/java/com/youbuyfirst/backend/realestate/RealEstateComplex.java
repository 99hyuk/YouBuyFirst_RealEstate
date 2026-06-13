package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "real_estate_complexes")
public class RealEstateComplex {

    @Id
    @Column(name = "target_id", length = 120)
    private String targetId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "region_target_id", length = 120)
    private String regionTargetId;

    @Column(name = "legal_dong_code", length = 20)
    private String legalDongCode;

    @Column(name = "road_address", length = 300)
    private String roadAddress;

    @Column(name = "jibun_address", length = 300)
    private String jibunAddress;

    @Column(name = "latitude", precision = 10, scale = 7)
    private BigDecimal latitude;

    @Column(name = "longitude", precision = 10, scale = 7)
    private BigDecimal longitude;

    @Column(name = "coordinate_provider", length = 80)
    private String coordinateProvider;

    @Column(name = "coordinate_as_of")
    private Instant coordinateAsOf;

    @Column(name = "coordinate_status", nullable = false, length = 30)
    private String coordinateStatus;

    @Column(name = "marker_tone", nullable = false, length = 20)
    private String markerTone;

    @Column(name = "price_summary", length = 80)
    private String priceSummary;

    @Column(name = "change_label", length = 40)
    private String changeLabel;

    @Column(name = "reaction_summary", length = 200)
    private String reactionSummary;

    @Column(name = "marker_note", length = 500)
    private String markerNote;

    @Column(name = "marker_data_status", nullable = false, length = 30)
    private String markerDataStatus;

    @Column(name = "marker_stale", nullable = false)
    private boolean markerStale;

    protected RealEstateComplex() {
    }

    public String getTargetId() {
        return targetId;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public String getRegionTargetId() {
        return regionTargetId;
    }

    public String getLegalDongCode() {
        return legalDongCode;
    }

    public String getRoadAddress() {
        return roadAddress;
    }

    public String getJibunAddress() {
        return jibunAddress;
    }

    public BigDecimal getLatitude() {
        return latitude;
    }

    public BigDecimal getLongitude() {
        return longitude;
    }

    public String getCoordinateProvider() {
        return coordinateProvider;
    }

    public Instant getCoordinateAsOf() {
        return coordinateAsOf;
    }

    public String getCoordinateStatus() {
        return coordinateStatus;
    }

    public String getMarkerTone() {
        return markerTone;
    }

    public String getPriceSummary() {
        return priceSummary;
    }

    public String getChangeLabel() {
        return changeLabel;
    }

    public String getReactionSummary() {
        return reactionSummary;
    }

    public String getMarkerNote() {
        return markerNote;
    }

    public String getMarkerDataStatus() {
        return markerDataStatus;
    }

    public boolean isMarkerStale() {
        return markerStale;
    }
}
