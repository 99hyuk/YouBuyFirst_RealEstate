alter table instruments
    add column exchange_code varchar(40);

create index idx_instruments_market_exchange_code
    on instruments (market, exchange_code);
