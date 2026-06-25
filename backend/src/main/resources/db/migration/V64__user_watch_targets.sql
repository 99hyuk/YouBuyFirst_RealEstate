create table user_watch_targets (
    id char(36) not null,
    user_id char(36) not null,
    target_type varchar(30) not null,
    target_id varchar(160) not null,
    display_name varchar(120) not null,
    landing_path varchar(600) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_user_watch_targets_user foreign key (user_id) references app_users (id),
    constraint uk_user_watch_targets_user_target unique (user_id, target_type, target_id)
);

create index idx_user_watch_targets_user_updated_at on user_watch_targets (user_id, updated_at, created_at);
