update content_items
set data_status = 'candidate',
    status_label = '출처 다양화 재검토',
    updated_at = current_timestamp
where content_type in ('report', 'video', 'link')
  and data_status = 'ok'
  and source_id in (
    'expert_report_search',
    'kbthink_column_search',
    'youtube:maeburitv',
    'youtube:jipconomy',
    'youtube:buiknam',
    'youtube:3protv'
  );
