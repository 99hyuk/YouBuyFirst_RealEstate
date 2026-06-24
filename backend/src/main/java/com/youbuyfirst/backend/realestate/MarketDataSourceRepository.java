package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface MarketDataSourceRepository extends JpaRepository<MarketDataSource, String> {
    List<MarketDataSource> findByEnabledTrueOrderByTitleAsc();
}
