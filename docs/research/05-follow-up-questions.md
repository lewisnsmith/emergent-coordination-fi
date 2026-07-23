# 05 — Secondary and exploratory questions

The expanded H1–H12 program is no longer a loose backlog. Its canonical experiment mapping is
[`configs/research-program.yaml`](../../configs/research-program.yaml). The items below are
secondary moderators or extensions; they must not silently enter the confirmatory family.

Secondary questions, ordered by proximity to the primary result. Experiment IDs below are
planned; only exp-000, exp-001, exp-002, and exp-010 currently have configs.

1. **Within-family vs cross-family convergence.** Does Claude agree with Claude more than with
   GPT/Gemini? Is there a "foundation-model fingerprint" detectable from trades alone?
   → provider-blocked MPHIQ/model-pair study (`exp-005` in the canonical catalog).
2. **Capability scaling.** Does convergence rise with model tier (small → frontier) or with
   reasoning effort? A "smarter agents find the same optimum" story vs "shared prior" story.
   → harness/capability robustness under `exp-009`; only dated frontier-eligible models.
3. **Temperature & sampling.** How much decorrelation does temperature buy, and at what
   performance and safety cost? (`exp-009`)
4. **Persona/demographic sensitivity.** Which instruction dimensions (risk tolerance, horizon,
   demographic framing, mandate) actually change *strategy* rather than *style*? How much
   dispersion can prompt engineering restore? (`exp-006`/`exp-008`)
5. **Information-set differentiation.** Does giving agents different news subsets decorrelate
   them more than personas do (H4)? What is the marginal substitution rate between information
   heterogeneity and prompt heterogeneity? (`exp-007`/`exp-008`)
6. **Memory & context.** Do agents with trade memory converge more over time (self-reinforcing
   strategies) or less (path dependence)? (exp-008)
7. **Regime dependence.** Is convergence stronger in crises (flight to the same safety) than in
   calm regimes? Compare synthetic regime blocks and historical windows. (exp-009)
8. **Shared-market amplification (H5).** Cascade frequency/depth vs cohort LLM-share: sweep the
   fraction of market capital held by LLM agents from 0% to 100%; find the threshold where
   price dynamics change. (exp-011)
9. **Tacit coordination / collusion.** In the shared market with market-maker LLM agents, do
   spreads widen supra-competitively without communication (Calvano-style)? (exp-012)
10. **Contamination.** Do agents behave differently on pre-cutoff vs post-cutoff vs synthetic
    data in ways consistent with memorization? (robustness battery attached to exp-001)
11. **Advisor mode.** If LLMs advise heterogeneous executors (humans with noise/latency) rather
    than trade directly, how much convergence survives the execution layer?
12. **Cross-market consistency.** Are the *same* models the convergence drivers in equities and
    prediction markets, or is convergence market-structure dependent?
13. **Detection.** Can a locked simulation-derived signature transport to held-out public tape?
    This is H9/`exp-018`–`019`; it cannot establish AI causation without H10/`exp-020` evidence.
14. **Decorrelation interventions.** Can information diversification, model-provider diversity,
    randomized execution, or human review reduce breadth without unacceptable performance or
    safety loss?
15. **Mechanism convergence.** Do agents reach similar trades through the same causally active
    features/circuits, or do distinct mechanisms converge behaviorally?
16. **Adversarial robustness.** Which injection, authority, FOMO, forced-certainty, anchoring,
    and conflicting-mandate prompts defeat grounding or constraint compliance?
