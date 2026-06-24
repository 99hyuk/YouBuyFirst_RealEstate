package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.MarketDataScheduleResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.YearMonth;
import java.time.format.DateTimeParseException;

@RestController
public class MarketDataScheduleController {

    private final MarketDataScheduleService service;

    public MarketDataScheduleController(MarketDataScheduleService service) {
        this.service = service;
    }

    @GetMapping("/api/realestate/market-data-schedules")
    public MarketDataScheduleResponse schedules(@RequestParam(required = false) String month) {
        return service.listMonth(parseMonth(month));
    }

    private YearMonth parseMonth(String value) {
        if (value == null || value.isBlank()) {
            return service.currentMonth();
        }
        try {
            return YearMonth.parse(value);
        } catch (DateTimeParseException exc) {
            return service.currentMonth();
        }
    }
}
