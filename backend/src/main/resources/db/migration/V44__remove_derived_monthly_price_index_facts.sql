-- Drop old derived R-ONE monthly index-change facts.
-- New ingestion stores raw monthly index values as fact_type='price_index'.

delete from map_layer_snapshots
where provider = 'reb'
  and (
      source_label = '한국부동산원 R-ONE 월간 아파트 매매가격지수'
      or source_label = 'REB R-ONE monthly apartment sale price index'
  );

delete from real_estate_market_facts
where provider = 'reb'
  and provider_dataset = 'reb_rone_monthly_apt_sale_price_index'
  and fact_type = 'sale_price_index_change_pct';
