# Sample size and power

An underpowered study does not merely fail to find an effect. It estimates the
effect wrongly in the direction of the interesting result, and it spends
participants to do it. Power is a design decision, taken while the protocol can
still change, and it is judged as a piece of reasoning rather than as a number.

Distilled from the `statistical-power` skill in K-Dense's Scientific Agent Skills
library (v1.1, MIT) - a source, not a skill installed alongside this one - with
Lakens (2022), Cohen (1988) and Arnold et al. (2011) as the underlying sources.

## Four quantities, locked together

Sample size, effect size, significance level and power are not four independent
choices. Fix any three and the fourth is determined. Every power calculation is
a rearrangement of that relationship, so the question is never "what n do I
need" but "which three am I fixing, and on what basis".

Conventional defaults are alpha = .05 two-sided and power = .80; .90 is common
in confirmatory and clinical work. State them rather than inheriting them.

**The calculation must describe the analysis you will actually run.** If the
planned analysis is a mixed model, a logistic regression, a survival model, or
anything with clustering, a t-test formula does not describe it and the number
it returns is not the study's sample size. Match the method to the model.

## Choosing the effect size

This is the input that makes or breaks the calculation, and the one most often
got wrong. A power analysis built on a guessed or inflated effect is worse than
none, because it carries false authority. In order of preference:

1. **The smallest effect that would change a decision** - the smallest effect
   size of interest. Anchor it to something external: the smallest difference
   that crosses a clinical threshold on a validated scale, the smallest effect
   that would justify adopting the intervention at its cost, or the effect below
   which you would call the result practically null. This is the most defensible
   basis, and it is the one `research-progression.md` already demands for a
   definitive trial: power to detect what matters, not what you hope to see.
2. **A prior estimate, shrunk.** Pilot and published effects are biased upward
   by publication bias and by the fact that the significant pilots are the ones
   that get followed up. Use the lower bound of the confidence interval rather
   than the point estimate, or apply an explicit safeguard, and never treat a
   single small pilot as a point estimate of the effect. This is the arithmetic
   behind the sizing error named in `research-progression.md`.
3. **A convention, last and labelled.** Cohen's small, medium and large are
   arbitrary and field-blind; they were never meant to substitute for domain
   knowledge. Use them only when nothing better exists, say so, and prefer
   "small" unless there is a reason.

## The sensitivity analysis is the deliverable

Recompute across a plausible range of effect sizes and report the range, or a
power curve. A required n presented as a single number conceals the dominant
source of uncertainty in the whole calculation - and a reader cannot tell
whether the study is robustly powered or balanced on one assumption.

Where n is already fixed by the setting, the useful quantity is the reverse: the
minimum detectable effect at that n. That is the honest answer to "could this
study have found anything", and it is a sensitivity statement, not a power
claim.

## Adjustments that are routinely forgotten

Each of these is the difference between a study powered on paper and a study
powered in practice. Apply them and say that you did.

- **Attrition.** Power gives the n to be *analysed*. Inflate the n to be
  *enrolled*: divide by one minus the expected dropout rate. At 20% dropout the
  enrol target is a quarter above the formula's answer.
- **Clustering.** Where observations are nested - patients in clinics, carers
  within a service - the effective sample size is smaller than the raw count.
  The design effect is 1 + (m - 1) x ICC for cluster size m. Treating clustered
  observations as independent is pseudoreplication and overstates power badly.
  For a cluster-randomised design, simulate rather than inflate a formula.
- **Multiplicity.** A Bonferroni-style correction raises n; powering each test at
  the corrected alpha is cruder than simulating the family-wise or FDR-controlled
  procedure directly, but either is better than powering the secondary endpoints
  as though they were primary. A study powered only for its primary outcome
  cannot support the secondary comparisons it reports.
- **Allocation.** Equal groups are the most efficient use of a fixed total. Where
  allocation is fixed by design, the calculation has to reflect it.
- **One- versus two-sided.** Two-sided is the default and almost always correct.
  A one-sided test buys power only by refusing to detect an effect in the
  unexpected direction, and it needs a justification.

## When there is no formula, simulate

Closed-form power exists for a handful of standard tests. For logistic and
Poisson regression, mixed and repeated-measures models, cluster-randomised
trials, survival analysis, mediation, and interactions, the method is
simulation, and the logic is always three steps:

1. Simulate a dataset from the assumed truth - the effect to be detected, plus
   realistic noise, baseline rates and cluster structure.
2. Analyse it with the exact model planned for the real data.
3. Repeat at least 1,000 times; 5,000 to 10,000 for a stable estimate near 80%.
   Power is the proportion of replicates in which the test is significant.

Report the Monte Carlo confidence interval on the estimate as well, so the
reader can tell whether .81 against .79 is a difference or simulation noise.
Dropout and clustering are then modelled inside the simulation rather than
tacked on afterwards, which is why simulation is the better route for any
design that has them.

## The post-hoc power trap

Do not compute power from the effect you have just estimated. Observed power is
a deterministic function of the p-value and carries no information the p-value
does not already carry; it is circular, and reviewers name it as such. If a
study is finished and the question is what it could have detected, report the
minimum detectable effect at the achieved n, or the confidence interval around
the observed effect. Do not produce observed power even if it is asked for
without flagging this.

## What the protocol has to state

A defensible power statement lets a reader reproduce the calculation without
asking you a question. It contains: the design and the planned analysis; the
effect size, its value, and the basis on which it was chosen; alpha and target
power, with sidedness; the resulting n per group and in total; the software and
version; any inflation for attrition, clustering or multiplicity, with the
assumptions used; and the sensitivity range. For a simulation, add the
data-generating assumptions, the number of replicates, and the Monte Carlo
interval.

This is the same standard `reporting-standards.md` sets for a sample-size
justification, and the same one `own-analysis.md` sets for any other number that
reaches a draft: the inputs are stated, and the reader can get back to them.

## Conversions and benchmarks

Required n is sensitive to the effect-size metric. A factor-of-two error in d
quarters or quadruples the sample size, and mixing d with f, or eta-squared with
f-squared, is the usual way it happens.

| Metric | Used for | Small | Medium | Large |
|---|---|---|---|---|
| d | mean differences | 0.20 | 0.50 | 0.80 |
| f | ANOVA | 0.10 | 0.25 | 0.40 |
| f-squared | regression, R-squared | 0.02 | 0.15 | 0.35 |
| r | correlation | 0.10 | 0.30 | 0.50 |
| eta-squared | variance explained | 0.01 | 0.06 | 0.14 |
| h | proportions, arcsine | 0.20 | 0.50 | 0.80 |
| w | chi-square | 0.10 | 0.30 | 0.50 |

The conversions that matter most in health services work:

- d to r: r = d / sqrt(d squared + 4), and back by d = 2r / sqrt(1 - r squared).
- d to f for two groups: f = d / 2.
- proportions to h: h = 2 x arcsin(sqrt(p1)) - 2 x arcsin(sqrt(p2)); this is what
  a two-proportion sample size is really computed on, not the raw difference.
- f-squared to R-squared, whole model: f-squared = R-squared / (1 - R-squared).
  For an increment, divide the added R-squared by 1 minus the full model's.
- odds ratio to log-odds: beta = log(OR), which is the coefficient to place in a
  simulated linear predictor.

A standardised effect is only as trustworthy as the SD it was divided by. Where
the raw difference and the SD are known, keep the calculation in raw units and
convert at the end. For paired designs the denominator is the SD of the
differences, which depends on the within-pair correlation, so a d from an
independent-groups study does not transfer.

## Where the calculation is done

Closed-form power for standard tests is available in software already in use -
`PROC POWER` and `PROC GLMPOWER` in SAS, `power` in Stata, `pwr` in R, and
dedicated tools such as G*Power and PASS. Simulation needs only the ability to
generate data and fit the planned model repeatedly. Whichever is used, the
software and version belong in the write-up, because the same inputs do not
always return the same n across packages and releases.
