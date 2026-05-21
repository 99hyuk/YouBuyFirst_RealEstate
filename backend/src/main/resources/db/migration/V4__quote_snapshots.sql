create table quote_snapshots (
    id bigint not null auto_increment,
    symbol varchar(40) not null,
    name varchar(200) not null,
    market varchar(20) not null,
    currency varchar(10) not null,
    price decimal(19, 6) not null,
    change_amount decimal(19, 6) not null,
    change_pct decimal(12, 4) not null,
    volume bigint not null,
    as_of datetime(6) not null,
    provider varchar(100) not null,
    delay_label varchar(120) not null,
    data_status varchar(30) not null,
    collected_at datetime(6) not null,
    primary key (id),
    constraint uk_quote_snapshots_symbol unique (symbol)
);

create index idx_quote_snapshots_market on quote_snapshots (market);
create index idx_quote_snapshots_as_of on quote_snapshots (as_of);
