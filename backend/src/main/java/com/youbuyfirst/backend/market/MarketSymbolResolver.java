package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.instrument.InstrumentIdentifier;
import com.youbuyfirst.backend.instrument.InstrumentIdentifierRepository;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

@Component
public class MarketSymbolResolver {

    private static final Set<String> KOSDAQ_CODES = Set.of(
            "035900",
            "086520",
            "196170",
            "247540"
    );

    private static final Map<String, MarketInstrument> KNOWN_INSTRUMENTS = knownInstruments();
    private static final Map<String, String> SYMBOL_ALIASES = symbolAliases();

    private final InstrumentIdentifierRepository identifierRepository;

    public MarketSymbolResolver(InstrumentIdentifierRepository identifierRepository) {
        this.identifierRepository = identifierRepository;
    }

    public MarketInstrument resolve(String value) {
        String symbol = normalizeProviderSymbol(value);
        return findMarketDataIdentifier(symbol)
                .map(this::toMarketInstrument)
                .orElseGet(() -> KNOWN_INSTRUMENTS.getOrDefault(symbol, infer(symbol)));
    }

    public String normalizeProviderSymbol(String value) {
        String normalized = normalizeKey(value);
        if (normalized.isBlank()) {
            return "";
        }
        String alias = SYMBOL_ALIASES.get(normalized);
        if (alias != null) {
            return alias;
        }
        if (normalized.contains(":")) {
            String[] parts = normalized.split(":", 2);
            String exchange = parts[0];
            String rawSymbol = parts[1];
            if (rawSymbol.matches("\\d{6}")) {
                return koreaSymbol(rawSymbol, "KOSDAQ".equals(exchange) || "KQ".equals(exchange));
            }
            return SYMBOL_ALIASES.getOrDefault(rawSymbol, rawSymbol);
        }
        if (normalized.matches("\\d{6}")) {
            return koreaSymbol(normalized, KOSDAQ_CODES.contains(normalized));
        }
        if (normalized.matches("\\d{6}\\.(KS|KQ)")) {
            return normalized;
        }
        return normalized.replace('.', '-');
    }

    public String providerName(String market) {
        return "KR".equalsIgnoreCase(market) ? "yfinance+FinanceDataReader" : "yfinance";
    }

    public String delayLabel(MarketInstrument instrument) {
        if ("KR".equalsIgnoreCase(instrument.market())) {
            return "Yahoo Finance delayed up to 30 min";
        }
        return "Yahoo Finance 10 min refresh snapshot";
    }

    public String exchangeTimezone(MarketInstrument instrument) {
        return "KR".equalsIgnoreCase(instrument.market()) ? "Asia/Seoul" : "America/New_York";
    }

    private MarketInstrument infer(String symbol) {
        if (symbol.endsWith(".KS") || symbol.endsWith(".KQ")) {
            return new MarketInstrument(symbol, symbol, "KR", "KRW");
        }
        return new MarketInstrument(symbol, symbol, "US", "USD");
    }

    private static String koreaSymbol(String code, boolean kosdaq) {
        return code + (kosdaq ? ".KQ" : ".KS");
    }

    private static String normalizeKey(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT).replace(" ", "");
    }

    private Optional<InstrumentIdentifier> findMarketDataIdentifier(String symbol) {
        return identifierRepository.findByNamespaceIgnoreCaseAndNormalizedIdentifierAndPurposeIgnoreCaseAndEnabledTrue(
                "YFINANCE",
                InstrumentIdentifier.normalizeIdentifier(symbol),
                "MARKET_DATA"
        );
    }

    private MarketInstrument toMarketInstrument(InstrumentIdentifier identifier) {
        Instrument instrument = identifier.getInstrument();
        String name = instrument.getNameEn() == null || instrument.getNameEn().isBlank()
                ? instrument.getNameKo()
                : instrument.getNameEn();
        return new MarketInstrument(
                instrument.getId(),
                identifier.getIdentifier(),
                name,
                instrument.getMarket(),
                currencyFor(instrument.getMarket())
        );
    }

    private static String currencyFor(String market) {
        return "KR".equalsIgnoreCase(market) ? "KRW" : "USD";
    }

    private static Map<String, MarketInstrument> knownInstruments() {
        Map<String, MarketInstrument> instruments = new HashMap<>();
        add(instruments, "005930.KS", "Samsung Electronics", "KR", "KRW");
        add(instruments, "000660.KS", "SK hynix", "KR", "KRW");
        add(instruments, "069500.KS", "KODEX 200", "KR", "KRW");
        add(instruments, "454910.KS", "Doosan Robotics", "KR", "KRW");
        add(instruments, "035420.KS", "NAVER", "KR", "KRW");
        add(instruments, "086520.KQ", "Ecopro", "KR", "KRW");
        add(instruments, "042700.KS", "Hanmi Semiconductor", "KR", "KRW");
        add(instruments, "066570.KS", "LG Electronics", "KR", "KRW");
        add(instruments, "005380.KS", "Hyundai Motor", "KR", "KRW");
        add(instruments, "006400.KS", "Samsung SDI", "KR", "KRW");
        add(instruments, "035720.KS", "Kakao", "KR", "KRW");
        add(instruments, "051910.KS", "LG Chem", "KR", "KRW");
        add(instruments, "068270.KS", "Celltrion", "KR", "KRW");
        add(instruments, "105560.KS", "KB Financial Group", "KR", "KRW");
        add(instruments, "055550.KS", "Shinhan Financial Group", "KR", "KRW");
        add(instruments, "005490.KS", "POSCO Holdings", "KR", "KRW");
        add(instruments, "207940.KS", "Samsung Biologics", "KR", "KRW");
        add(instruments, "247540.KQ", "Ecopro BM", "KR", "KRW");
        add(instruments, "035900.KQ", "JYP Entertainment", "KR", "KRW");
        add(instruments, "196170.KQ", "Alteogen", "KR", "KRW");
        add(instruments, "133690.KS", "TIGER 200", "KR", "KRW");
        add(instruments, "102110.KS", "TIGER 200", "KR", "KRW");

        add(instruments, "AAPL", "Apple", "US", "USD");
        add(instruments, "MSFT", "Microsoft", "US", "USD");
        add(instruments, "NVDA", "NVIDIA", "US", "USD");
        add(instruments, "TSLA", "Tesla", "US", "USD");
        add(instruments, "AMZN", "Amazon", "US", "USD");
        add(instruments, "GOOGL", "Alphabet", "US", "USD");
        add(instruments, "META", "Meta Platforms", "US", "USD");
        add(instruments, "NFLX", "Netflix", "US", "USD");
        add(instruments, "AVGO", "Broadcom", "US", "USD");
        add(instruments, "AMD", "Advanced Micro Devices", "US", "USD");
        add(instruments, "JPM", "JPMorgan Chase", "US", "USD");
        add(instruments, "BRK-B", "Berkshire Hathaway", "US", "USD");
        add(instruments, "SOFI", "SoFi Technologies", "US", "USD");
        add(instruments, "PLTR", "Palantir", "US", "USD");
        add(instruments, "TSM", "Taiwan Semiconductor Manufacturing", "US", "USD");
        add(instruments, "SMR", "NuScale Power", "US", "USD");
        add(instruments, "SPY", "SPDR S&P 500 ETF Trust", "US", "USD");
        add(instruments, "QQQ", "Invesco QQQ Trust", "US", "USD");
        add(instruments, "SOXS", "Direxion Daily Semiconductor Bear 3X Shares", "US", "USD");
        add(instruments, "MSFU", "Direxion Daily MSFT Bull 2X Shares", "US", "USD");
        return Map.copyOf(instruments);
    }

    private static Map<String, String> symbolAliases() {
        Map<String, String> aliases = new HashMap<>();
        for (String symbol : KNOWN_INSTRUMENTS.keySet()) {
            aliases.put(symbol, symbol);
            aliases.put(symbol.replace(".KS", ""), symbol);
            aliases.put(symbol.replace(".KQ", ""), symbol);
        }
        aliases.put("KRX:005930", "005930.KS");
        aliases.put("KOSPI:005930", "005930.KS");
        aliases.put("KOSDAQ:086520", "086520.KQ");
        aliases.put("BRK.B", "BRK-B");
        aliases.put("BRK-B", "BRK-B");
        return Map.copyOf(aliases);
    }

    private static void add(
            Map<String, MarketInstrument> instruments,
            String symbol,
            String name,
            String market,
            String currency
    ) {
        instruments.put(symbol, new MarketInstrument(symbol, name, market, currency));
    }
}
