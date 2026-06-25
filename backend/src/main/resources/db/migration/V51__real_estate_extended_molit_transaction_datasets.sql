insert into real_estate_public_data_datasets (
    dataset_id, provider, provider_name, owner_org, display_name, fact_type, access_method, response_format,
    source_url, endpoint_url, target_granularity, date_granularity, refresh_interval, stale_after_hours,
    priority, backfill_required, enabled_for_backfill, source_row_count, notes, created_at, updated_at
) values
    (
        'molit_offi_trade', 'molit', '국토교통부', '국토교통부', '오피스텔 매매 실거래가', 'offi_trade', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade',
        'https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade',
        'sigungu', 'month', 'daily-check', 72,
        21, true, true, null, 'LAWD_CD and DEAL_YMD based officetel sale transactions.', now(6), now(6)
    ),
    (
        'molit_offi_rent', 'molit', '국토교통부', '국토교통부', '오피스텔 전월세 실거래가', 'offi_rent', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent',
        'https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent',
        'sigungu', 'month', 'daily-check', 72,
        22, true, true, null, 'LAWD_CD and DEAL_YMD based officetel rent transactions.', now(6), now(6)
    ),
    (
        'molit_rh_trade', 'molit', '국토교통부', '국토교통부', '연립다세대 매매 실거래가', 'rh_trade', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade',
        'https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade',
        'sigungu', 'month', 'daily-check', 72,
        23, true, true, null, 'LAWD_CD and DEAL_YMD based rowhouse/multifamily sale transactions.', now(6), now(6)
    ),
    (
        'molit_rh_rent', 'molit', '국토교통부', '국토교통부', '연립다세대 전월세 실거래가', 'rh_rent', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent',
        'https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent',
        'sigungu', 'month', 'daily-check', 72,
        24, true, true, null, 'LAWD_CD and DEAL_YMD based rowhouse/multifamily rent transactions.', now(6), now(6)
    ),
    (
        'molit_sh_trade', 'molit', '국토교통부', '국토교통부', '단독다가구 매매 실거래가', 'sh_trade', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade',
        'sigungu', 'month', 'daily-check', 72,
        25, true, true, null, 'LAWD_CD and DEAL_YMD based single/multifamily house sale transactions.', now(6), now(6)
    ),
    (
        'molit_sh_rent', 'molit', '국토교통부', '국토교통부', '단독다가구 전월세 실거래가', 'sh_rent', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent',
        'sigungu', 'month', 'daily-check', 72,
        26, true, true, null, 'LAWD_CD and DEAL_YMD based single/multifamily house rent transactions.', now(6), now(6)
    ),
    (
        'molit_silv_trade', 'molit', '국토교통부', '국토교통부', '분양권 매매 실거래가', 'silv_trade', 'openapi', 'xml',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSilvTrade/getRTMSDataSvcSilvTrade',
        'https://apis.data.go.kr/1613000/RTMSDataSvcSilvTrade/getRTMSDataSvcSilvTrade',
        'sigungu', 'month', 'daily-check', 72,
        27, true, true, null, 'LAWD_CD and DEAL_YMD based presale-right sale transactions.', now(6), now(6)
    )
on duplicate key update
    provider = values(provider),
    provider_name = values(provider_name),
    owner_org = values(owner_org),
    display_name = values(display_name),
    fact_type = values(fact_type),
    access_method = values(access_method),
    response_format = values(response_format),
    source_url = values(source_url),
    endpoint_url = values(endpoint_url),
    target_granularity = values(target_granularity),
    date_granularity = values(date_granularity),
    refresh_interval = values(refresh_interval),
    stale_after_hours = values(stale_after_hours),
    priority = values(priority),
    backfill_required = values(backfill_required),
    enabled_for_backfill = values(enabled_for_backfill),
    source_row_count = values(source_row_count),
    notes = values(notes),
    updated_at = now(6);
