update content_items
set data_status = 'candidate',
    status_label = '기준 재검토',
    updated_at = current_timestamp
where content_type in ('report', 'video', 'link')
and source_id in (
    'expert_report_search',
    'kbthink_column_search',
    'youtube:maeburitv',
    'youtube:jipconomy',
    'youtube:buiknam',
    'youtube:3protv'
)
and data_status = 'ok';
