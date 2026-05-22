create table investor_flow_snapshots (
    id bigint not null auto_increment,
    symbol varchar(40) not null,
    name varchar(200) not null,
    market varchar(20) not null,
    currency varchar(10) not null,
    trade_date date not null,
    provider varchar(100) not null,
    source_label varchar(200) not null,
    delay_label varchar(120) not null,
    as_of datetime(6) not null,
    data_status varchar(30) not null,
    collected_at datetime(6) not null,
    individual_net_amount decimal(19, 2) not null,
    individual_net_volume bigint not null,
    foreign_net_amount decimal(19, 2) not null,
    foreign_net_volume bigint not null,
    institution_net_amount decimal(19, 2) not null,
    institution_net_volume bigint not null,
    primary key (id),
    constraint uk_investor_flow_snapshots_symbol unique (symbol)
);

create index idx_investor_flow_snapshots_trade_date on investor_flow_snapshots (trade_date);
create index idx_investor_flow_snapshots_as_of on investor_flow_snapshots (as_of);
