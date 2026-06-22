from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicy,
    SourcePolicyRegistry,
    SourceStatus,
    default_source_policy_registry,
    runtime_environment_from_env,
)


def test_unknown_source_defaults_to_disabled():
    registry = SourcePolicyRegistry({})

    decision = registry.decide("UNKNOWN", CrawlRuntimeEnvironment.LOCAL)

    assert decision.allowed is False
    assert decision.policy.source == "UNKNOWN"
    assert decision.policy.status == SourceStatus.DISABLED
    assert "default disabled" in decision.reason


def test_default_registry_marks_current_mvp_sources_local_research_only():
    registry = default_source_policy_registry()

    naver = registry.policy_for("NAVER")
    naver_cafe = registry.policy_for("NAVER_CAFE")
    daum_cafe = registry.policy_for("DAUM_CAFE")
    fmkorea = registry.policy_for("FMKOREA")

    assert naver.status == SourceStatus.LOCAL_RESEARCH_ONLY
    assert naver_cafe.status == SourceStatus.LOCAL_RESEARCH_ONLY
    assert daum_cafe.status == SourceStatus.LOCAL_RESEARCH_ONLY
    assert fmkorea.status == SourceStatus.LOCAL_RESEARCH_ONLY


def test_local_research_source_runs_only_in_local_runtime():
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy(
                source="NAVER",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="local research only",
            )
        }
    )

    local_decision = registry.decide("NAVER", CrawlRuntimeEnvironment.LOCAL)
    public_decision = registry.decide("NAVER", CrawlRuntimeEnvironment.PUBLIC)

    assert local_decision.allowed is True
    assert public_decision.allowed is False
    assert "not allowed in public runtime" in public_decision.reason


def test_public_demo_and_disabled_sources_never_run():
    registry = SourcePolicyRegistry(
        {
            "DEMO": SourcePolicy("DEMO", SourceStatus.PUBLIC_DEMO_ONLY, "demo source"),
            "OFF": SourcePolicy("OFF", SourceStatus.DISABLED, "disabled source"),
        }
    )

    for runtime in (CrawlRuntimeEnvironment.LOCAL, CrawlRuntimeEnvironment.PUBLIC):
        assert registry.decide("DEMO", runtime).allowed is False
        assert registry.decide("OFF", runtime).allowed is False


def test_enabled_source_runs_in_local_and_public_runtime():
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )

    assert registry.decide("SAFE", CrawlRuntimeEnvironment.LOCAL).allowed is True
    assert registry.decide("SAFE", CrawlRuntimeEnvironment.PUBLIC).allowed is True


def test_runtime_environment_parsing_fails_closed_to_public():
    assert runtime_environment_from_env("local") == CrawlRuntimeEnvironment.LOCAL
    assert runtime_environment_from_env("LOCAL") == CrawlRuntimeEnvironment.LOCAL
    assert runtime_environment_from_env("public") == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env(None) == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env("") == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env("staging") == CrawlRuntimeEnvironment.PUBLIC
