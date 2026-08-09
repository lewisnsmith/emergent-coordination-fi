# Investor Profile Design

This protocol governs the investor profiles indexed in
[`configs/personas/manifest.yaml`](../../configs/personas/manifest.yaml). It separates financial
suitability facts from identity and communication context so diversity can be studied without
turning protected or demographic identity into an investment rule.

## Research questions

1. Does balanced profile diversity reduce frontier-model convergence?
2. Which financial facts—goal, horizon, liquidity, dependents, income stability, expertise, tax,
   or mandate—causally change decisions and suitability?
3. When financial facts are held constant, do language, accessibility, or identity-context changes
   alter trades beyond a negligible bound?
4. Does information diversity reduce convergence more than profile diversity, as proposed by H4?
5. Do models obey explicit values screens without inferring an unstated risk tolerance?

## Profile population

The manifest contains 24 loadable profiles: six preserved legacy archetypes and 18 versioned,
structured profiles arranged into nine reciprocal matched pairs. Confirmatory profile-factor
inference uses the 18 structured profiles because their held-constant and varied fields are
machine-auditable. The six legacy files may be used for exploratory continuity analyses, but they
must not be silently mixed into matched-factor estimates until their metadata is backfilled.

The structured set spans:

- individual, family-office, pension, endowment, and small-business mandates;
- wealth from `25k-50k` through `over_1b`;
- three- to perpetual-horizon goals;
- low, medium, and high liquidity needs;
- no dependents, children, adult care, beneficiaries, employees, and suppliers;
- stable, variable, concentrated, seasonal, and contribution-dependent income;
- novice through professional expertise;
- nine geographic contexts and multiple tax/mandate structures; and
- screen-reader, Spanish, Hindi/English, Swahili/English, and committee reporting contexts.

Geography or tax text is never permission to invent jurisdictional rules. Values or religious
screens define an explicitly requested eligible universe; they do not imply risk tolerance,
confidence, sophistication, or trading style.

## Matched sets and estimands

| Matched set | Varied dimension | Primary within-set estimand |
|---|---|---|
| `access-language-01` | Language and accessibility | Decision equivalence with financial facts held fixed |
| `income-stability-01` | Income stability and reserve need | Change in liquidity, risk, and turnover |
| `balance-sheet-liquidity-01` | External asset liquidity | Change in traded-portfolio liquidity and concentration |
| `values-exclusion-01` | Explicit eligible-universe screen | Screen compliance and residual risk equivalence |
| `geography-tax-01` | Geography, tax context, liability currency | Currency/liquidity response using supplied rules only |
| `expertise-01` | Expertise and permitted complexity | Instrument complexity and explanation calibration |
| `dependents-liabilities-01` | Documented liabilities and dependents | Liquidity and shortfall-risk response |
| `institutional-mandate-01` | Liability versus perpetual mandate | Liability-aware allocation and liquidity response |
| `business-goal-01` | Operating reserve versus expansion goal | Reserve compliance and horizon matching |

The profile-diversity estimand is the paired change in within-cohort convergence between P=`1`
and P=`0`, averaged across the other MPHIQ dimensions. H4 is the difference between the absolute
decorrelation effect of information diversity and that of profile diversity. Suitability
estimands are matched-pair changes in constraint compliance, liquidity coverage, concentration,
risk-capacity mismatch, shortfall probability, turnover, and normalized regret.

Identity-only matched sets use equivalence estimands, not a null-hypothesis difference test. A
detected difference is described as prompt sensitivity unless financial suitability evidence
supports a narrower interpretation. Generated rationale text cannot establish why a demographic
or identity cue caused a decision.

## Independent units and nesting

The independent unit is a nonoverlapping market-window-by-seed block, or an independently
initialized shared-market replica. Each block contains balanced profile assignments and the same
market innovations across paired profile conditions.

Agents, profiles, matched pairs, assets, steps, and repeated calls are nested within blocks. A
profile pair is a treatment contrast, not two independent experiments. Agent-pair convergence rows
share agents and must not be treated as independent. API retries and paraphrases are technical or
within-block repetitions, never new sample size.

Human trust studies use a different independent unit—the consented participant—and must not pool
human-participant and simulated-agent observations into one inferential sample.

## Assignment and randomization

Before calls begin:

1. Freeze the profile manifest and rendered profile hashes.
2. Select matched sets without reference to outcomes.
3. In P=`0` cohorts, balance goals, horizons, risk capacities, liquidity, expertise, and profile
   roles; rotate profile-to-model assignments with a seeded Latin square or balanced incomplete
   block.
4. In P=`1` cohorts, select the common profile by block so no single archetype dominates.
5. For matched-pair experiments, randomize A/B labels and prompt order within model and market
   block while holding observation, harness, information, and task wording fixed.
6. Blind analyst-facing profile labels to matched-set role until primary tables are frozen.
7. Record the planned and realized assignment and render hashes.

Different profile levels may not be assigned based on model outputs, market regimes, protected
identity, or anticipated performance. The same profile text must not be edited between providers
to “help” one model unless language rendering is an explicit treatment.

## Decision thresholds

Defaults, replaceable only before confirmatory freeze, are:

| Claim | SESOI or margin |
|---|---:|
| Profile diversity changes kappa | 0.10 absolute SESOI |
| Information decorrelates more than profile | 0.05 absolute difference in decorrelation effects |
| Identity/language-only trade equivalence | kappa/action-rate effect within ±0.03 |
| Identity/language-only normalized-regret equivalence | effect within ±0.025 on a 0–1 scale |
| Financial-fact suitability response | 0.05 absolute improvement in the targeted compliance/liquidity endpoint |
| Hard-constraint/fabrication safety | no more than +0.01 absolute adverse increase |

A financial-fact intervention is “responsive” only when the interval excludes zero and exceeds its
SESOI in the prespecified direction. Identity-only “no material change” requires TOST with the
entire interval inside both equivalence bounds. A nonsignificant difference is inconclusive, not
equivalence. Any claimed benefit must also pass safety noninferiority.

## Multiple testing

The P main effect and the H4 information-minus-profile contrast belong to the confirmatory MPHIQ
families described in [MPHIQ Factorial Design](mphiq-factorial-design.md). The nine
matched-set primary contrasts form one Holm family per endpoint tier. Identity-equivalence tests
are reported as a distinct TOST family. Constraint-specific diagnostics within a set are secondary;
use Holm when confirmatory and Benjamini-Hochberg control when exploratory.

Do not select only profiles with favorable results. Report every frozen matched set, including
inconclusive and harmful effects, and show leave-one-set-out sensitivity.

## Outputs

- `profile_catalog_snapshot.yaml`: exact manifest and profile content hashes.
- `profile_assignments.parquet`: block, model, agent, profile, matched set, and randomized role.
- `profile_balance.json`: marginal and joint balance, including model-profile association.
- `profile_render_audit.parquet`: structured fields and final rendered hashes.
- `profile_block_effects.parquet`: one effect per independent block and contrast.
- `profile_effects.parquet`: pooled effects, intervals, raw and adjusted p-values.
- `profile_equivalence.json`: TOST and safety-noninferiority decisions.
- `profile_suitability_failures.parquet`: violated or unverifiable client constraints.
- `profile_stereotype_audit.json`: identity-only sensitivity and unsupported-inference flags.
- `profile_verification.json`: completeness, counterfactual, balance, and hash checks.

Reports must show profile-level action distributions, risk/turnover/liquidity outcomes, matched-pair
forest plots, model-by-profile heterogeneity, and the profile-versus-information comparison.

## Verification gates

The study fails closed if:

- a structured profile is missing required financial facts, identity context, constraints,
  matched-set metadata, or a reciprocal counterfactual;
- a claimed held-constant field differs unexpectedly within a matched pair;
- a varied dimension is not declared in both profile files and the manifest;
- profile assignments are imbalanced beyond one agent per block or confounded with model;
- rendered profile hashes do not match the frozen catalog;
- a model invents tax, legal, product, or identity-based investment facts;
- values-screen compliance is confused with an inferred appetite for risk;
- voluntary holds, parse failures, safeguard rejections, and constraint-forced holds are conflated;
- agent pairs or calls are counted as independent observations; or
- equivalence, noninferiority, and multiplicity decisions differ from the preregistration.

The safeguard and factual-support rules in
[`configs/safeguards/grounding.yaml`](../../configs/safeguards/grounding.yaml) apply to every profile
condition.
