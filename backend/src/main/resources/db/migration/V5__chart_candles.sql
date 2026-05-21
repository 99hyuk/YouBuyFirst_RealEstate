create table chart_candle_sets (
    id bigint not null auto_increment,
    symbol varchar(40) not null,
    name varchar(200) not null,
    market varchar(20) not null,
    currency varchar(10) not null,
    range_label varchar(10) not null,
    candle_interval varchar(10) not null,
    provider varchar(100) not null,
    delay_label varchar(120) not null,
    as_of datetime(6) not null,
    data_status varchar(30) not null,
    collected_at datetime(6) not null,
    primary key (id),
    constraint uk_chart_candle_sets_symbol_range_interval unique (symbol, range_label, candle_interval)
);

create table chart_candles (
    id bigint not null auto_increment,
    set_id bigint not null,
    trade_date date not null,
    open_price decimal(19, 6) not null,
    high_price decimal(19, 6) not null,
    low_price decimal(19, 6) not null,
    close_price decimal(19, 6) not null,
    volume bigint not null,
    primary key (id),
    constraint fk_chart_candles_set foreign key (set_id) references chart_candle_sets (id),
    constraint uk_chart_candles_set_date unique (set_id, trade_date)
);

create index idx_chart_candle_sets_symbol on chart_candle_sets (symbol);
create index idx_chart_candle_sets_as_of on chart_candle_sets (as_of);
create index idx_chart_candles_trade_date on chart_candles (trade_date);
