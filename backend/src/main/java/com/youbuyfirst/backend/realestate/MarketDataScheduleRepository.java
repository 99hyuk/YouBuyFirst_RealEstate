package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.Collection;
import java.util.List;

public interface MarketDataScheduleRepository extends JpaRepository<MarketDataSchedule, String> {
    List<MarketDataSchedule> findByScheduleDateBetweenOrderByScheduleDateAscTitleAsc(LocalDate start, LocalDate end);

    long deleteByScheduleDateBetween(LocalDate start, LocalDate end);

    long deleteByScheduleDateBetweenAndIdNotIn(LocalDate start, LocalDate end, Collection<String> ids);
}
