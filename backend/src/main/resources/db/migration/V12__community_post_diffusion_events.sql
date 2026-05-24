create table community_post_diffusion_events (
    id bigint not null auto_increment,
    post_id bigint,
    source varchar(40) not null,
    external_id varchar(200) not null,
    board_id varchar(120),
    diffusion_type varchar(40) not null,
    list_position integer,
    observed_at datetime(6) not null,
    view_count integer,
    recommend_count integer,
    comment_count integer,
    diffusion_only boolean not null default false,
    crawl_run_id varchar(160),
    created_at datetime(6) not null,
    primary key (id),
    constraint uk_post_diffusion_source_external_type_observed unique (source, external_id, diffusion_type, observed_at),
    constraint fk_post_diffusion_post foreign key (post_id) references community_posts (id) on delete cascade
);

create index idx_post_diffusion_source_board_observed
    on community_post_diffusion_events (source, board_id, observed_at);

create index idx_post_diffusion_post_observed
    on community_post_diffusion_events (post_id, observed_at);
