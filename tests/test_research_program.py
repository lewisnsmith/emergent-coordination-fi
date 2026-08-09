from flock.core.research import (
    CostPolicy,
    ExperimentSpec,
    HighCostComponent,
    HypothesisSpec,
    ResearchProgram,
    validate_research_program,
)


def cost_policy(**components: HighCostComponent) -> CostPolicy:
    return CostPolicy(
        hypothesis_retention="required",
        rule="cost may change staging or evidence strategy but may never delete a hypothesis",
        allowed_actions=["mark_high_cost", "defer_execution"],
        removal_gate=(
            "removal requires a scientific rationale unrelated to cost and a "
            "preregistration amendment"
        ),
        high_cost_components=components,
    )


def test_research_program_rejects_unknown_hypothesis_and_missing_contract(tmp_path):
    program = ResearchProgram(
        version="test",
        cost_policy=cost_policy(),
        hypotheses={
            "H1": HypothesisSpec(question="q", claim="c", claim_boundary="b")
        },
        experiments={
            "exp-x": ExperimentSpec(
                name="x",
                hypotheses=["H404"],
                mode="simulation",
                question="q",
                status="scaffolded",
                estimand="e",
                independent_unit="window",
            )
        },
    )
    result = validate_research_program(program, tmp_path)
    assert not result.ok
    assert any("unknown hypotheses" in error for error in result.errors)
    assert any("no verification contract" in error for error in result.errors)
    assert any("no output contract" in error for error in result.errors)


def test_external_study_dependency_warning_is_visible():
    program = ResearchProgram(
        version="test",
        cost_policy=cost_policy(),
        hypotheses={
            "H6": HypothesisSpec(question="q", claim="c", claim_boundary="b")
        },
        experiments={
            "exp-017": ExperimentSpec(
                name="trust",
                hypotheses=["H6"],
                mode="human_subjects",
                question="q",
                status="blocked_external",
                estimand="e",
                independent_unit="participant",
                outputs=["claims.json"],
                verification=["IRB gate"],
            )
        },
    )
    result = validate_research_program(program)
    assert result.ok
    assert result.warnings


def test_cost_policy_rejects_unknown_references():
    program = ResearchProgram(
        version="test",
        cost_policy=cost_policy(
            expensive=HighCostComponent(
                hypotheses=["H404"],
                experiments=["exp-404"],
                cost_driver="unknown work",
            )
        ),
        hypotheses={
            "H1": HypothesisSpec(question="q", claim="c", claim_boundary="b")
        },
        experiments={},
    )
    result = validate_research_program(program)
    assert not result.ok
    assert any("unknown hypotheses" in error for error in result.errors)
    assert any("unknown experiments" in error for error in result.errors)
