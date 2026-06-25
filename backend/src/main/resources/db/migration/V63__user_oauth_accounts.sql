create table user_oauth_accounts (
    id char(36) not null,
    user_id char(36) not null,
    provider varchar(40) not null,
    provider_user_id varchar(128) not null,
    email varchar(255),
    display_name varchar(100),
    created_at datetime(6) not null,
    last_login_at datetime(6) not null,
    primary key (id),
    constraint fk_user_oauth_accounts_user foreign key (user_id) references app_users (id),
    constraint uk_user_oauth_provider_subject unique (provider, provider_user_id)
);

create index idx_user_oauth_accounts_user_id on user_oauth_accounts (user_id);
