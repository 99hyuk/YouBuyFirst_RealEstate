insert into real_estate_market_data_targets (
    target_id, provider, provider_dataset, lawd_code, enabled, refresh_interval_hours, stale_after_hours, created_at, updated_at
)
select
    region.target_id,
    'molit',
    dataset.provider_dataset,
    region.legal_dong_code,
    true,
    24,
    72,
    '2026-06-25 00:00:00',
    '2026-06-25 00:00:00'
from real_estate_regions region
join (
    select 'molit_apt_trade' as provider_dataset
    union all select 'molit_apt_rent'
    union all select 'molit_offi_trade'
    union all select 'molit_offi_rent'
    union all select 'molit_rh_trade'
    union all select 'molit_rh_rent'
    union all select 'molit_sh_trade'
    union all select 'molit_sh_rent'
    union all select 'molit_silv_trade'
) dataset
where region.target_id in ('region-seoul-jongno', 'region-seoul-mapo')
  and region.legal_dong_code is not null
  and length(region.legal_dong_code) = 5
on duplicate key update
    enabled = values(enabled),
    refresh_interval_hours = values(refresh_interval_hours),
    stale_after_hours = values(stale_after_hours),
    updated_at = values(updated_at);
