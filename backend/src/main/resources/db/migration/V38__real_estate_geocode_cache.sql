create table real_estate_geocode (
    id bigint not null auto_increment,
    query_key varchar(255) not null,
    lat double,
    lng double,
    resolved boolean not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_real_estate_geocode_query unique (query_key)
);
