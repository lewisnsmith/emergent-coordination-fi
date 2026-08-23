# H7 adoption threshold forecast

## Question

Given verified adoption observations and a separately estimated synthetic market-impact threshold,
what calibrated distribution describes possible threshold-crossing times?

## Design

Keep adoption measurement and the synthetic threshold as distinct versioned inputs. Adoption data
must define its construct, population, sampling, revisions, and rights. Consume the full
`market_threshold_distribution.json`, including uncertainty and no-threshold mass. Evaluate frozen
diffusion and baseline models at rolling forecast origins without later-origin leakage.

## Estimands, units, and controls

Report rolling-origin error and calibration plus an ensemble distribution over conditional
crossing time and no-crossing probability. The independent unit is an adoption series or forecast
origin. Naive and trend baselines, alternative diffusion forms, source/vintage sensitivity, and
explicit scenario labels are required controls.

## Failure rules and limits

Invalid adoption constructs, revision leakage, missing threshold uncertainty, or failed rolling
calibration blocks the forecast. Proxies cannot establish actual AI-managed capital, a synthetic
threshold is not a real-market threshold, and scenarios are not facts about future adoption.

## Execution sequence

1. Define the adoption construct and resolve source, lineage, revision, and release requirements.
2. Verify the upstream synthetic threshold and preserve its claim boundary.
3. Freeze series, vintages, transformations, missingness, origins, and model rules.
4. Gate data acquisition, spending, protocol inspection, and release rights.
5. Run rolling-origin evaluation before the final conditional forecast.
6. Release calibration failures, null crossing mass, and alternative scenarios identically.
