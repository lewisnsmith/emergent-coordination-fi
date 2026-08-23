# H10 and H11 attribution and release

## Question

Under verified exposure and a credible counterfactual, does AI exposure cause preregistered market
changes, and can all resulting evidence tiers be released without overstating causal status?

## Design

Exp-021 joins the noncausal detection panel to independently verified exposure and a fixed
assignment or quasi-experimental design. Detection never substitutes for exposure. Exp-022 builds
versioned, separately labeled simulation-truth, signature-event, exposure, and causally verified
tiers. A failed identification study remains releasable without a causal tier or empty placeholder.

## Estimands, units, and controls

Use the design-specific causal estimand at the frozen institution-market-time exposure unit;
repeated rows are nested. Mandatory controls are pretrends, placebo dates and assets, spillover
checks, clustered uncertainty, exposure provenance, and confounding sensitivity. Each dataset tier
receives independent lineage, leakage, utility, uncertainty, and checksum validation.

## Failure rules and limits

Unverified exposure, no credible counterfactual, failed pretrends or placebos, unresolved
spillovers, or missing rights prevents causal labeling. Dataset tiers must never be collapsed.
Failed identification is a valid result and does not invalidate upstream simulation or detection
releases.

## Execution sequence

1. Verify upstream releases and separately acquire and audit exposure evidence.
2. Fix the identification design, independent unit, estimand, and falsifications.
3. Gate data acquisition, spending, protocol inspection, storage, and release rights.
4. Run exp-021 and assign causal status only after every identification gate passes.
5. Build exp-022 tiers independently; omit unavailable tiers rather than fabricate placeholders.
6. Release negative, null, failed-identification, and causal findings under the same provenance rules.
