update content_items
set data_status = 'candidate',
    status_label = '기준 재검토',
    updated_at = current_timestamp
where (
    content_type = 'video'
    and (
        source_id in ('manual_curated:youtube', 'youtube:maeburitv', 'youtube:jipconomy', 'youtube:butv', 'serpapi:google_news')
        or url like '%/shorts/%'
    )
)
or (
    content_type = 'link'
    and source_id in ('manual_curated:blog', 'google_news_blog_search', 'tistory:news8253', 'serpapi:google_news')
)
or (
    content_type = 'report'
    and (
        source_id in ('manual_curated:report', 'serpapi:google_news')
        or (source_id = 'google_news_rss' and data_status = 'ok')
    )
);
