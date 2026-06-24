update content_items
set data_status = 'ok',
    updated_at = current_timestamp
where content_type in ('report', 'video', 'link')
  and data_status = 'candidate'
  and source_id in (
    'report:kb-research',
    'report:hanaif',
    'report:wfri',
    'report:hf-kif',
    'report:official-research',
    'kbthink_column_search',
    'naver_blog:ppassong',
    'naver_blog:building-standard',
    'tistory:auctionguide',
    'youtube:maeburitv',
    'youtube:jipconomy',
    'youtube:buiknam',
    'youtube:3protv',
    'youtube:smarttube',
    'youtube:kimjagga'
  );
