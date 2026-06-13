package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "map_features")
public class MapFeature {

    @Id
    @Column(length = 160)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "boundary_asset_id", insertable = false, updatable = false)
    private MapBoundaryAsset boundaryAsset;

    @Column(name = "boundary_asset_id", nullable = false, length = 120)
    private String boundaryAssetId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @Column(name = "layer_type", nullable = false, length = 30)
    private String layerType;

    @Column(name = "geometry_id", nullable = false, length = 120)
    private String geometryId;

    @Column(name = "region_code", nullable = false, length = 30)
    private String regionCode;

    @Column(name = "parent_region_code", length = 30)
    private String parentRegionCode;

    protected MapFeature() {
    }

    public String getId() {
        return id;
    }

    public MapBoundaryAsset getBoundaryAsset() {
        return boundaryAsset;
    }

    public String getBoundaryAssetId() {
        return boundaryAssetId;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getLayerType() {
        return layerType;
    }

    public String getGeometryId() {
        return geometryId;
    }

    public String getRegionCode() {
        return regionCode;
    }

    public String getParentRegionCode() {
        return parentRegionCode;
    }
}
