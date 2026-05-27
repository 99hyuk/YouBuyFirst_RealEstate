package com.youbuyfirst.backend.instrument;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

@Component
public class InstrumentMasterSeedLoader implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(InstrumentMasterSeedLoader.class);
    private static final String SOURCE = "instrument-master-seed";

    private final InstrumentRepository instrumentRepository;
    private final InstrumentIdentifierRepository identifierRepository;
    private final ResourceLoader resourceLoader;
    private final TransactionTemplate transactionTemplate;
    private final boolean enabled;
    private final String seedPath;

    public InstrumentMasterSeedLoader(
            InstrumentRepository instrumentRepository,
            InstrumentIdentifierRepository identifierRepository,
            ResourceLoader resourceLoader,
            TransactionTemplate transactionTemplate,
            @Value("${app.instrument.master-seed.enabled:true}") boolean enabled,
            @Value("${app.instrument.master-seed.path:classpath:data/instrument-master-seed.tsv}") String seedPath
    ) {
        this.instrumentRepository = instrumentRepository;
        this.identifierRepository = identifierRepository;
        this.resourceLoader = resourceLoader;
        this.transactionTemplate = transactionTemplate;
        this.enabled = enabled;
        this.seedPath = seedPath;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (!enabled) {
            return;
        }
        Resource resource = resourceLoader.getResource(seedPath);
        if (!resource.exists()) {
            log.warn("Instrument master seed resource does not exist: {}", seedPath);
            return;
        }
        List<SeedRow> rows = readRows(resource);
        if (rows.isEmpty()) {
            return;
        }
        transactionTemplate.executeWithoutResult(status -> loadRows(rows));
    }

    private void loadRows(List<SeedRow> rows) {
        Map<String, Instrument> instruments = instrumentRepository.findAll()
                .stream()
                .collect(Collectors.toMap(
                        instrument -> instrumentKey(instrument.getMarket(), instrument.getSymbol()),
                        Function.identity(),
                        (first, second) -> first,
                        LinkedHashMap::new
                ));

        List<Instrument> instrumentsToSave = new ArrayList<>();
        for (SeedRow row : rows) {
            Instrument instrument = instruments.get(row.instrumentKey());
            if (instrument == null) {
                instrument = new Instrument(
                        row.market(),
                        row.symbol(),
                        row.displayName(),
                        row.nameEn(),
                        row.type(),
                        row.exchangeCode()
                );
                instruments.put(row.instrumentKey(), instrument);
                instrumentsToSave.add(instrument);
            } else if (instrument.applySeed(row.nameKo(), row.nameEn(), row.type(), row.exchangeCode())) {
                instrumentsToSave.add(instrument);
            }
        }
        if (!instrumentsToSave.isEmpty()) {
            instrumentRepository.saveAll(instrumentsToSave);
            instrumentRepository.flush();
        }

        Set<String> identifierKeys = identifierRepository.findAll()
                .stream()
                .map(identifier -> identifierKey(
                        identifier.getNamespace(),
                        identifier.getIdentifier(),
                        identifier.getPurpose()
                ))
                .collect(Collectors.toCollection(LinkedHashSet::new));
        List<InstrumentIdentifier> identifiersToSave = new ArrayList<>();
        Instant now = Instant.now();
        for (SeedRow row : rows) {
            Instrument instrument = instruments.get(row.instrumentKey());
            addIdentifier(
                    identifiersToSave,
                    identifierKeys,
                    instrument,
                    "YFINANCE",
                    row.yfinanceSymbol(),
                    "MARKET_DATA",
                    row.sourceSnapshot(),
                    now
            );
            addIdentifier(
                    identifiersToSave,
                    identifierKeys,
                    instrument,
                    "KR".equals(row.market()) ? "KRX_TICKER" : "US_TICKER",
                    row.exchangeSymbol(),
                    "EXCHANGE_REFERENCE",
                    row.sourceSnapshot(),
                    now
            );
            if ("KR".equals(row.market())) {
                addIdentifier(
                        identifiersToSave,
                        identifierKeys,
                        instrument,
                        "NAVER_STOCK_BOARD",
                        row.boardSymbol(),
                        "COMMUNITY_BOARD",
                        row.sourceSnapshot(),
                        now
                );
            }
        }
        if (!identifiersToSave.isEmpty()) {
            identifierRepository.saveAll(identifiersToSave);
        }
    }

    private void addIdentifier(
            List<InstrumentIdentifier> identifiersToSave,
            Set<String> identifierKeys,
            Instrument instrument,
            String namespace,
            String identifier,
            String purpose,
            String notes,
            Instant now
    ) {
        if (isBlank(identifier)) {
            return;
        }
        String key = identifierKey(namespace, identifier, purpose);
        if (!identifierKeys.add(key)) {
            return;
        }
        identifiersToSave.add(new InstrumentIdentifier(
                instrument,
                namespace,
                identifier,
                purpose,
                SOURCE,
                true,
                notes,
                now
        ));
    }

    private List<SeedRow> readRows(Resource resource) {
        List<SeedRow> rows = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
            String header = reader.readLine();
            if (!isExpectedHeader(header)) {
                throw new IllegalStateException("invalid instrument master seed header: " + header);
            }
            String line;
            int lineNumber = 1;
            while ((line = reader.readLine()) != null) {
                lineNumber += 1;
                if (line.isBlank()) {
                    continue;
                }
                String[] parts = line.split("\t", -1);
                if (parts.length != 10) {
                    throw new IllegalStateException("invalid instrument master seed row at line " + lineNumber);
                }
                rows.add(SeedRow.from(parts, lineNumber));
            }
        } catch (IOException exception) {
            throw new IllegalStateException("failed to read instrument master seed: " + seedPath, exception);
        }
        return rows;
    }

    private static boolean isExpectedHeader(String header) {
        return "market\tsymbol\tname_ko\tname_en\ttype\texchange\tyfinance_symbol\texchange_symbol\tboard_symbol\tsource_snapshot"
                .equals(header);
    }

    private static String instrumentKey(String market, String symbol) {
        return normalizeToken(market) + "\u0000" + normalizeToken(symbol);
    }

    private static String identifierKey(String namespace, String identifier, String purpose) {
        return normalizeToken(namespace)
                + "\u0000"
                + InstrumentIdentifier.normalizeIdentifier(identifier)
                + "\u0000"
                + normalizeToken(purpose);
    }

    private static String normalizeToken(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private record SeedRow(
            String market,
            String symbol,
            String nameKo,
            String nameEn,
            String type,
            String exchangeCode,
            String yfinanceSymbol,
            String exchangeSymbol,
            String boardSymbol,
            String sourceSnapshot
    ) {
        static SeedRow from(String[] parts, int lineNumber) {
            String market = normalizeToken(parts[0]);
            String symbol = normalizeToken(parts[1]);
            String type = normalizeToken(parts[4]);
            if (market.isBlank() || symbol.isBlank() || type.isBlank()) {
                throw new IllegalStateException("instrument master seed row misses required fields at line " + lineNumber);
            }
            return new SeedRow(
                    market,
                    symbol,
                    trimToNull(parts[2]),
                    trimToNull(parts[3]),
                    type,
                    trimToNull(parts[5]),
                    trimToNull(parts[6]),
                    trimToNull(parts[7]),
                    trimToNull(parts[8]),
                    trimToNull(parts[9])
            );
        }

        String instrumentKey() {
            return InstrumentMasterSeedLoader.instrumentKey(market, symbol);
        }

        String displayName() {
            if (!isBlank(nameKo)) {
                return nameKo;
            }
            if (!isBlank(nameEn)) {
                return nameEn;
            }
            return symbol;
        }
    }
}
