alter table community_posts
    add column board_id varchar(120);

alter table community_posts
    add column view_count integer;

alter table community_posts
    add column recommend_count integer;

alter table community_posts
    add column comment_count integer;

create index idx_posts_source_board_published_at on community_posts (source, board_id, published_at);
