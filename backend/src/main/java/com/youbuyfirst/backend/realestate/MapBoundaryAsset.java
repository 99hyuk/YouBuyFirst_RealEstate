package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "map_boundary_assets")
public class MapBoundaryAsset {

    @Id
    @Column(length = 120)
    private String id;

    @Column(name = "asset_type", nullable = false, length = 60)
    private String assetType;

    @Column(name = "source_label", nullable = false, length = 160)
    private String sourceLabel;

    @Column(name = "base_year", length = 20)
    private String baseYear;

    @Column(name = "asset_url", length = 500)
    private String assetUrl;

    @Column(name = "imported_at", nullable = false)
    private Instant importedAt;

    protected MapBoundaryAsset() {
    }

    public String getId() {
        return id;
    }

    public String getAssetType() {
        return assetType;
    }

    public String getSourceLabel() {
        return sourceLabel;
    }

    public String getBaseYear() {
        return baseYear;
    }

    public String getAssetUrl() {
        return assetUrl;
    }

    public Instant getImportedAt() {
        return importedAt;
    }
}
