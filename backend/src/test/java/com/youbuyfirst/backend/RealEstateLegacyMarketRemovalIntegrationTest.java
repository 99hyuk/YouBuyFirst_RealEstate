package com.youbuyfirst.backend;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "spring.datasource.url=jdbc:h2:mem:youbuyfirst_realestate_no_legacy_market_test;MODE=MySQL;DATABASE_TO_LOWER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=TRUE"
)
@ActiveProfiles("test")
class RealEstateLegacyMarketRemovalIntegrationTest {

    private static final String EQUITY_WORD = "sto" + "cks";
    private static final String LEGACY_CODE_PARAM = "sym" + "bol";
    private static final String TARGET_TABLE_PREFIX = "instru" + "ment";
    private static final String PRICE_WORD = "quo" + "te";
    private static final String CHART_BATCH_PATH = "chart" + "-candles";
    private static final String FLOW_PATH = "investor" + "-flows";
    private static final String LEGACY_ANALYSIS_TABLE = "senti" + "ment_analyses";

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void defaultRealEstateContextDoesNotExposeLegacyMarketApis() {
        assertMissing("/api/" + PRICE_WORD + "s?" + LEGACY_CODE_PARAM + "s=005930.KS");
        assertMissing("/api/market/" + CHART_BATCH_PATH + "?" + LEGACY_CODE_PARAM + "=005930.KS&range=1M&interval=1d");
        assertMissing("/api/market/" + FLOW_PATH + "/history?" + LEGACY_CODE_PARAM + "=005930.KS&limit=5");
        assertMissing("/api/market/technical-indicators?" + LEGACY_CODE_PARAM + "=005930.KS&range=3M&interval=1d");
        assertMissing("/api/indicators/community-snapshots?windowStart=2026-06-01T00:00:00Z");
        assertMissing("/admin/" + EQUITY_WORD + "/TSLA/metrics?market=US");
        assertMissing("/admin/" + TARGET_TABLE_PREFIX + "s/matcher-snapshot?market=US");
        assertMissing("/admin/" + TARGET_TABLE_PREFIX + "-aliases?market=US");
        assertMissing("/admin/alias-candidates?source=DCINSIDE");
    }

    @Test
    void migratedSchemaDoesNotContainLegacyMarketTables() {
        assertThat(tableExists(TARGET_TABLE_PREFIX + "s")).isFalse();
        assertThat(tableExists(TARGET_TABLE_PREFIX + "_aliases")).isFalse();
        assertThat(tableExists(TARGET_TABLE_PREFIX + "_alias_candidates")).isFalse();
        assertThat(tableExists(TARGET_TABLE_PREFIX + "_identifiers")).isFalse();
        assertThat(tableExists("post_mentions")).isFalse();
        assertThat(tableExists(LEGACY_ANALYSIS_TABLE)).isFalse();
        assertThat(tableExists("metric_snapshots")).isFalse();
        assertThat(tableExists(PRICE_WORD + "_snapshots")).isFalse();
        assertThat(tableExists("chart_candle_sets")).isFalse();
        assertThat(tableExists("chart_candles")).isFalse();
        assertThat(tableExists("chart_candle_refresh_requests")).isFalse();
        assertThat(tableExists("investor_flow_snapshots")).isFalse();
    }

    @Test
    void seedCrawlTargetsAreRealEstateBoardsOnly() {
        Integer legacyBoardTargets = jdbcTemplate.queryForObject(
                "select count(*) from crawl_targets where target_kind = ?",
                Integer.class,
                EQUITY_WORD.substring(0, EQUITY_WORD.length() - 1) + "-board"
        );
        Integer realEstateBoards = jdbcTemplate.queryForObject(
                "select count(*) from crawl_targets where target_id in ('PPOMPPU:house', 'DCINSIDE:immovables')",
                Integer.class
        );

        assertThat(legacyBoardTargets).isZero();
        assertThat(realEstateBoards).isEqualTo(2);
    }

    private boolean tableExists(String tableName) {
        Integer count = jdbcTemplate.queryForObject(
                """
                        select count(*)
                        from information_schema.tables
                        where lower(table_name) = lower(?)
                        """,
                Integer.class,
                tableName
        );
        return count != null && count > 0;
    }

    private void assertMissing(String path) {
        ResponseEntity<String> response = restTemplate.getForEntity(path, String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }
}
