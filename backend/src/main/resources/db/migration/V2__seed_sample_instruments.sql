insert into instruments (market, symbol, name_ko, name_en, type) values
('KR', '005930', '삼성전자', 'Samsung Electronics', 'STOCK'),
('KR', '000660', 'SK하이닉스', 'SK Hynix', 'STOCK'),
('US', 'TSLA', '테슬라', 'Tesla', 'STOCK'),
('US', 'NVDA', '엔비디아', 'NVIDIA', 'STOCK'),
('US', 'SPY', 'SPY ETF', 'SPDR S&P 500 ETF Trust', 'ETF');

insert into instrument_aliases (instrument_id, alias)
select i.id, a.alias
from instruments i
join (
    select '005930' as symbol, '삼전' as alias union all
    select '005930', '삼성전자' union all
    select '000660', '하닉' union all
    select '000660', 'SK하이닉스' union all
    select 'TSLA', '테슬라' union all
    select 'TSLA', 'TSLA' union all
    select 'NVDA', '엔비디아' union all
    select 'NVDA', '엔비' union all
    select 'NVDA', 'NVDA' union all
    select 'SPY', 'SPY'
) a on i.symbol = a.symbol;
