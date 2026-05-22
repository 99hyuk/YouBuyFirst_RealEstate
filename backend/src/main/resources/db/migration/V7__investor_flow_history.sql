alter table investor_flow_snapshots
    drop index uk_investor_flow_snapshots_symbol;

alter table investor_flow_snapshots
    add constraint uk_investor_flow_snapshots_symbol_trade_date unique (symbol, trade_date);

create index idx_investor_flow_snapshots_symbol_trade_date
    on investor_flow_snapshots (symbol, trade_date);
