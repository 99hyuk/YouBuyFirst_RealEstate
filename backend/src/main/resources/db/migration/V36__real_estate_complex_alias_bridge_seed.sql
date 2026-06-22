insert into real_estate_aliases (
    target_id, target_type, alias, normalized_alias, alias_type, source, evidence_url,
    confidence, review_state, ambiguous, created_by, created_at, updated_at
)
select seed.target_id, seed.target_type, seed.alias, seed.normalized_alias, seed.alias_type,
       seed.source, seed.evidence_url, seed.confidence, seed.review_state, seed.ambiguous,
       seed.created_by, seed.created_at, seed.updated_at
from (
    select 'complex-mapo-raemian-prugio' target_id, 'complex' target_type, '마래푸' alias, '마래푸' normalized_alias, 'community_slang' alias_type, 'seed:complex-alias-bridge' source, null evidence_url, 0.86 confidence, 'approved' review_state, false ambiguous, 'seed' created_by, '2026-06-17 00:00:00' created_at, '2026-06-17 00:00:00' updated_at
    union all select 'complex-mapo-raemian-prugio', 'complex', '아현동 마래푸', '아현동마래푸', 'nearby_short_name', 'seed:complex-alias-bridge', null, 0.88, 'approved', false, 'seed', '2026-06-17 00:00:00', '2026-06-17 00:00:00'
    union all select 'complex-mapo-raemian-prugio', 'complex', '마포 래미안 푸르지오', '마포래미안푸르지오', 'spaced_official', 'seed:complex-alias-bridge', null, 0.90, 'approved', false, 'seed', '2026-06-17 00:00:00', '2026-06-17 00:00:00'
    union all select 'complex-mapo-raemian-prugio', 'complex', '아현동 마포 래미안 푸르지오', '아현동마포래미안푸르지오', 'nearby_area', 'seed:complex-alias-bridge', null, 0.90, 'approved', false, 'seed', '2026-06-17 00:00:00', '2026-06-17 00:00:00'
) seed
join real_estate_targets target on target.id = seed.target_id
where not exists (
    select 1
    from real_estate_aliases existing
    where existing.target_id = seed.target_id
      and existing.normalized_alias = seed.normalized_alias
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type,
    confidence, source, review_state, created_at, updated_at
)
select community_target.id, 'complex', canonical_target.id, 'complex', 'same_living_area',
       0.82, 'seed:canonical-name-bridge', 'approved', '2026-06-17 00:00:00', '2026-06-17 00:00:00'
from real_estate_targets community_target
join real_estate_targets canonical_target
  on canonical_target.id <> community_target.id
 and canonical_target.target_type = 'complex'
 and canonical_target.review_state = 'approved'
 and canonical_target.data_status in ('ok', 'partial')
 and canonical_target.normalized_name = community_target.normalized_name
where community_target.target_type = 'complex'
  and community_target.data_status = 'community_observed'
  and not exists (
      select 1
      from real_estate_target_edges existing
      where existing.from_target_id = community_target.id
        and existing.to_target_id = canonical_target.id
        and existing.edge_type = 'same_living_area'
  );
