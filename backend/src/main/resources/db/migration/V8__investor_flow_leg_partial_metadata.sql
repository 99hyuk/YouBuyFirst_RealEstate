alter table investor_flow_snapshots
    modify column individual_net_amount decimal(19, 2);

alter table investor_flow_snapshots
    modify column foreign_net_amount decimal(19, 2);

alter table investor_flow_snapshots
    modify column institution_net_amount decimal(19, 2);

alter table investor_flow_snapshots
    add column individual_derived boolean not null default false;

alter table investor_flow_snapshots
    add column foreign_derived boolean not null default false;

alter table investor_flow_snapshots
    add column institution_derived boolean not null default false;
