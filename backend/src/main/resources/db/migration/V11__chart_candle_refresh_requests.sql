create table chart_candle_refresh_requests (
    id bigint not null auto_increment,
    symbol varchar(40) not null,
    range_label varchar(10) not null,
    candle_interval varchar(10) not null,
    status varchar(30) not null,
    requested_at datetime(6) not null,
    last_attempt_at datetime(6),
    completed_at datetime(6),
    error_message varchar(500),
    primary key (id),
    constraint uk_chart_candle_refresh_requests_symbol_range_interval unique (symbol, range_label, candle_interval)
);

create index idx_chart_candle_refresh_requests_status_requested
    on chart_candle_refresh_requests (status, requested_at);
