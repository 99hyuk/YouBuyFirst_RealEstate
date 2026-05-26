alter table quote_snapshots
    add column instrument_id bigint;

alter table chart_candle_sets
    add column instrument_id bigint;

alter table chart_candle_refresh_requests
    add column instrument_id bigint;

alter table investor_flow_snapshots
    add column instrument_id bigint;

alter table crawl_targets
    add column instrument_id bigint;

update quote_snapshots qs
set instrument_id = (
    select min(ii.instrument_id)
    from instrument_identifiers ii
    where ii.normalized_identifier = upper(replace(qs.symbol, ' ', ''))
      and ii.enabled = true
      and (
          (ii.namespace = 'YFINANCE' and ii.purpose = 'MARKET_DATA')
          or (ii.namespace in ('KRX_TICKER', 'US_TICKER') and ii.purpose = 'EXCHANGE_REFERENCE')
      )
)
where instrument_id is null;

update chart_candle_sets ccs
set instrument_id = (
    select min(ii.instrument_id)
    from instrument_identifiers ii
    where ii.normalized_identifier = upper(replace(ccs.symbol, ' ', ''))
      and ii.enabled = true
      and (
          (ii.namespace = 'YFINANCE' and ii.purpose = 'MARKET_DATA')
          or (ii.namespace in ('KRX_TICKER', 'US_TICKER') and ii.purpose = 'EXCHANGE_REFERENCE')
      )
)
where instrument_id is null;

update chart_candle_refresh_requests ccr
set instrument_id = (
    select min(ii.instrument_id)
    from instrument_identifiers ii
    where ii.normalized_identifier = upper(replace(ccr.symbol, ' ', ''))
      and ii.enabled = true
      and (
          (ii.namespace = 'YFINANCE' and ii.purpose = 'MARKET_DATA')
          or (ii.namespace in ('KRX_TICKER', 'US_TICKER') and ii.purpose = 'EXCHANGE_REFERENCE')
      )
)
where instrument_id is null;

update investor_flow_snapshots ifs
set instrument_id = (
    select min(ii.instrument_id)
    from instrument_identifiers ii
    where ii.normalized_identifier = upper(replace(ifs.symbol, ' ', ''))
      and ii.enabled = true
      and (
          (ii.namespace = 'YFINANCE' and ii.purpose = 'MARKET_DATA')
          or (ii.namespace in ('KRX_TICKER', 'US_TICKER') and ii.purpose = 'EXCHANGE_REFERENCE')
      )
)
where instrument_id is null;

update crawl_targets ct
set instrument_id = (
    select min(ii.instrument_id)
    from instrument_identifiers ii
    where ii.namespace = 'NAVER_STOCK_BOARD'
      and ii.normalized_identifier = upper(replace(ct.symbol, ' ', ''))
      and ii.purpose = 'COMMUNITY_BOARD'
      and ii.enabled = true
)
where instrument_id is null
  and ct.source = 'NAVER'
  and ct.symbol is not null;

create index idx_quote_snapshots_instrument
    on quote_snapshots (instrument_id);

create index idx_chart_candle_sets_instrument
    on chart_candle_sets (instrument_id, range_label, candle_interval);

create index idx_chart_candle_refresh_requests_instrument
    on chart_candle_refresh_requests (instrument_id, range_label, candle_interval);

create index idx_investor_flow_snapshots_instrument
    on investor_flow_snapshots (instrument_id, trade_date);

create index idx_crawl_targets_instrument
    on crawl_targets (instrument_id);

alter table quote_snapshots
    add constraint fk_quote_snapshots_instrument foreign key (instrument_id) references instruments (id);

alter table chart_candle_sets
    add constraint fk_chart_candle_sets_instrument foreign key (instrument_id) references instruments (id);

alter table chart_candle_refresh_requests
    add constraint fk_chart_candle_refresh_requests_instrument foreign key (instrument_id) references instruments (id);

alter table investor_flow_snapshots
    add constraint fk_investor_flow_snapshots_instrument foreign key (instrument_id) references instruments (id);

alter table crawl_targets
    add constraint fk_crawl_targets_instrument foreign key (instrument_id) references instruments (id);
