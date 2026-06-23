package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

/**
 * 단지 검색 문자열(query_key)별 좌표 캐시. 카카오 지오코딩 결과를 한 번 저장해
 * 재요청을 막는다. resolved=false는 "조회했으나 좌표를 못 찾음"을 의미한다.
 */
@Entity
@Table(
        name = "real_estate_geocode",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_geocode_query",
                columnNames = {"query_key"}
        )
)
public class RealEstateGeocode {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "query_key", nullable = false, length = 255)
    private String queryKey;

    @Column
    private Double lat;

    @Column
    private Double lng;

    @Column(nullable = false)
    private boolean resolved;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateGeocode() {
    }

    public RealEstateGeocode(String queryKey, Double lat, Double lng, boolean resolved, Instant updatedAt) {
        this.queryKey = queryKey;
        this.lat = lat;
        this.lng = lng;
        this.resolved = resolved;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public String getQueryKey() {
        return queryKey;
    }

    public Double getLat() {
        return lat;
    }

    public Double getLng() {
        return lng;
    }

    public boolean isResolved() {
        return resolved;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
