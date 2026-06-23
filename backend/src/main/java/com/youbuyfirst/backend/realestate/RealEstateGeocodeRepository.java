package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface RealEstateGeocodeRepository extends JpaRepository<RealEstateGeocode, Long> {

    List<RealEstateGeocode> findByQueryKeyIn(Collection<String> queryKeys);
}
