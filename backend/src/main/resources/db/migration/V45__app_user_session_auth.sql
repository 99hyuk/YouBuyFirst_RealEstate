create table app_users (
    id char(36) not null,
    username varchar(20) not null,
    email varchar(255) not null,
    display_name varchar(20) not null,
    password_hash varchar(255) not null,
    auth_provider varchar(40) not null,
    role varchar(30) not null,
    status varchar(30) not null,
    created_at datetime(6) not null,
    last_seen_at datetime(6),
    primary key (id),
    constraint uk_app_users_username unique (username),
    constraint uk_app_users_email unique (email),
    constraint uk_app_users_display_name unique (display_name)
);

create index idx_app_users_last_seen_at on app_users (last_seen_at);
