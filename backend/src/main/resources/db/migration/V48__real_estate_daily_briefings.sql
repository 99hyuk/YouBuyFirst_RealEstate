create table daily_briefings (
    id varchar(120) not null,
    briefing_date date not null,
    title varchar(200) not null,
    summary_headlines_json text not null,
    focus_regions_json text not null,
    model_name varchar(80),
    prompt_version varchar(80),
    generated_at datetime(6) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id)
);

create table daily_briefing_sections (
    id varchar(160) not null,
    briefing_id varchar(120) not null,
    section_key varchar(80) not null,
    title varchar(120) not null,
    body text not null,
    display_order integer not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_daily_briefing_sections_briefing foreign key (briefing_id) references daily_briefings (id)
);

create table daily_briefing_source_items (
    id varchar(160) not null,
    briefing_id varchar(120) not null,
    source_type varchar(40) not null,
    ref_id varchar(160),
    label varchar(160),
    title varchar(300) not null,
    url varchar(1000),
    display_order integer not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_daily_briefing_source_items_briefing foreign key (briefing_id) references daily_briefings (id)
);

create index idx_daily_briefings_date_generated on daily_briefings (briefing_date, generated_at);
create index idx_daily_briefings_generated on daily_briefings (generated_at);
create index idx_daily_briefing_sections_briefing on daily_briefing_sections (briefing_id, display_order);
create index idx_daily_briefing_source_items_briefing on daily_briefing_source_items (briefing_id, display_order);
