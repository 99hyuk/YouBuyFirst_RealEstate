alter table instrument_alias_candidates
    add column reviewer varchar(80);

alter table instrument_alias_candidates
    add column review_notes varchar(500);

alter table instrument_alias_candidates
    add column reviewed_at datetime(6);
