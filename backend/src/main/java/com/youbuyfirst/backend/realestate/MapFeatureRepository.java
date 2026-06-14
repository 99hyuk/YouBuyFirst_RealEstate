package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface MapFeatureRepository extends JpaRepository<MapFeature, String> {

    List<MapFeature> findByLayerTypeOrderByRegionCodeAsc(String layerType);

    @Query("""
            select new com.youbuyfirst.backend.realestate.MapLayerSnapshotRow(
                feature.targetId,
                target.targetType,
                target.displayName,
                target.slug,
                region.regionLevel,
                feature.regionCode,
                region.legalDongCode,
                region.parentRegionId,
                feature.geometryId,
                snapshot.periodKey,
                snapshot.changePct,
                snapshot.sampleCount,
                snapshot.confidence,
                snapshot.asOf,
                snapshot.provider,
                snapshot.sourceLabel,
                snapshot.dataStatus,
                snapshot.stale,
                asset.sourceLabel
            )
            from MapFeature feature
            join feature.target target
            join feature.boundaryAsset asset
            left join RealEstateRegion region on region.targetId = feature.targetId
            join MapLayerSnapshot snapshot on snapshot.targetId = feature.targetId
                and snapshot.layerType = feature.layerType
            where feature.layerType = :layerType
                and (:parentRegionCode is null or feature.parentRegionCode = :parentRegionCode)
                and snapshot.asOf = (
                    select max(latest.asOf)
                    from MapLayerSnapshot latest
                    where latest.targetId = feature.targetId
                        and latest.layerType = feature.layerType
                        and latest.periodKey = snapshot.periodKey
                )
            order by feature.regionCode asc, snapshot.periodKey asc
            """)
    List<MapLayerSnapshotRow> findLatestLayerRows(
            @Param("layerType") String layerType,
            @Param("parentRegionCode") String parentRegionCode
    );
}
