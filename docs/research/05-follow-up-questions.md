# 05 — Follow-up Questions

Backlog of secondary research questions, each mapping to an experiment axis or planned config.
Ordered roughly by how directly they extend the primary result.

1. **Within-family vs cross-family convergence.** Does Claude agree with Claude more than with
   GPT/Gemini? Is there a "foundation-model fingerprint" detectable from trades alone?
   → replay sweeps with provider-blocked cohorts; classifier: predict provider from decision
   stream (exp-003).
2. **Capability scaling.** Does convergence rise with model tier (small → frontier) or with
   reasoning effort? A "smarter agents find the same optimum" story vs "shared prior" story.
   → tier-blocked sweeps (exp-004).
3. **Temperature & sampling.** How much decorrelation does temperature buy, and at what
   performance cost? (exp-005)
4. **Persona/demographic sensitivity.** Which instruction dimensions (risk tolerance, horizon,
   demographic framing, mandate) actually change *strategy* rather than *style*? How much
   dispersion can prompt engineering restore? (exp-006)
5. **Information-set differentiation.** Does giving agents different news subsets decorrelate
   them more than personas do (H4)? What is the marginal substitution rate between information
   heterogeneity and prompt heterogeneity? (exp-007)
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
13. **Detection.** Can a market observer detect LLM-cohort presence from public tape alone
    (herding signatures, order-timing regularities)? Useful for surveillance policy.
