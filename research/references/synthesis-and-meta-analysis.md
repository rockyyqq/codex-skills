# Synthesis and meta-analysis

Source: *Cochrane Handbook for Systematic Reviews of Interventions*, version
5.0.1 (Higgins & Green, eds., 2008 print edition). The current online Handbook
is a later major version: the risk-of-bias tool has been replaced (RoB 2 for
trials, ROBINS-I for non-randomised studies), the GRADE guidance has been
extended, the search chapters rewritten, and new chapters added. **The
statistical principles below are stable; the tool names, chapter numbers and
default software behaviour are not.** Check the current version before citing
the Handbook, and cite the version you used.

`evidence-appraisal.md` covers what each design can support. This file covers
what happens once a reader tries to combine results, and where the arithmetic
quietly stops supporting the sentence it is attached to.

## Decide whether to pool at all

A systematic review need not contain a meta-analysis. Where effects differ in
**direction**, an average is not a summary of the evidence - it is a number that
no population experiences. Say that, present the studies, and explain what
distinguishes them. A narrative synthesis with a table is a legitimate answer.

Before pooling, check that the studies share a comparator, an outcome
definition, a population and a time horizon close enough that a single effect
means something. Statistical consistency is not the test of that; clinical
judgement is.

## Effect measures

| Measure | Use | Trap |
|---|---|---|
| Mean difference (MD) | Same outcome, same scale and units | None if the scale really is the same |
| Standardised mean difference (SMD) | Same construct, different instruments | Not comparable across different constructs; 0.2/0.5/0.8 are conventions, not measurements |
| Odds ratio (OR) | Dichotomous outcomes, case-control | Homogeneous ORs necessarily imply heterogeneous risk differences, and vice versa |
| Risk ratio (RR) | Dichotomous outcomes | Same instability of the risk difference; RR is more stable across baseline risk than RD |
| Risk difference (RD) | Absolute effect, decision-making | Least stable across baseline risks; rarely appropriate to pool |
| Hazard ratio (HR) | Time-to-event | Assumes proportional hazards; useless where curves cross or the assumption is untested |
| Peto OR | Rare events, few or zero cells | Performs well for rare events; do not use it for common events or unbalanced arms |

Counts of events that can recur are not dichotomies. Analysing them as
proportions discards the exposure time and produces a unit-of-analysis error.

## Unit of analysis: match the arithmetic to what was randomised

The number of observations in the analysis should equal the number of units
randomised. Every entry below breaks that rule unless it is handled, and all of
them produce confidence intervals that are too narrow - which reads as a
precise finding.

- **Cluster-randomised** (schools, clinics, villages, carers within a clinic):
  the design effect is `1 + (M - 1) × ICC`, where *M* is the average cluster
  size. Divide the sample size by it to get the effective sample size, or use a
  multilevel model. Without an ICC from the study or a defensible external one,
  the analysis cannot be done properly - say so.
- **Cross-over trials:** participants act as their own controls, so the paired
  analysis needs the within-person correlation. Treating the arms as independent
  groups understates the variance.
- **Repeated measurements:** more than one timepoint per study cannot be entered
  as if independent. Either obtain individual patient data and analyse the whole
  trajectory, define separate outcomes per timepoint (and label them), pick one
  clinically important timepoint in advance, or take the longest follow-up and
  accept the heterogeneity that induces. Choosing the timepoint that maximises
  the data available is a reporting-bias risk - say so if you do it.
- **Multiple treatment attempts** (fertility cycles, readmissions): the
  denominator is participants, not attempts. `n` cycles is not `n`.
- **Multiple body parts, split-mouth designs:** sites within a person are
  clustered; sites receiving different interventions resemble a cross-over.
- **Multiple intervention groups sharing one control:** including "dose 1 vs
  control" and "dose 2 vs control" in the same analysis counts the control group
  twice. Combine groups, split the control, or use one comparison and name the
  others.

## Fixed-effect or random-effects

- **Fixed-effect** answers "what is the best estimate of a single common
  effect?" - and if effects genuinely differ, it can produce an estimate that
  exists in no population, with a confidence interval that is too narrow.
- **Random-effects** answers "what is the average effect across a distribution?"
  It gives relatively more weight to small studies, which is exactly what you do
  not want when small studies are biased or selectively published. Where
  small-study effects are plausible, random-effects *exacerbates* them.

Three rules that survive the version changes:

1. **Never choose the model on the basis of a test for heterogeneity.** Choose
   it on the question and the assumption you are willing to defend.
2. Report whether the other model would have changed the conclusion. If it
   would, the conclusion depends on the model, and that belongs in the text.
3. RevMan's default random-effects method (DerSimonian-Laird) has confidence
   intervals that are slightly too narrow because they ignore the uncertainty in
   the estimated between-study variance. With few studies or small studies with
   few events, the widths matter - Hartung-Knapp-Sidik-Jonkman or a Bayesian
   approach in other software is the alternative to name.

## Heterogeneity: three numbers, three different jobs

- **Chi-squared (Cochran's Q)**, and its *p*: a test of whether the differences
  exceed chance. It has low power with few or small studies, so a
  non-significant result must never be read as homogeneity; the convention of
  testing at 0.10 rather than 0.05 exists for that reason.
- **I²** is the percentage of variability in the effect estimates attributable
  to heterogeneity rather than sampling error. It is not the proportion of
  agreement, and it does not tell you whether pooling makes sense. The Handbook's
  bands overlap deliberately - 0-40% might not be important, 30-60% may be
  moderate, 50-90% may be substantial, 75-100% considerable - and their
  importance depends on the magnitude and direction of the effect and on the
  strength of evidence for heterogeneity. Do not report I² alone.
- **Tau² (τ²)** is the between-study variance; its square root is the standard
  deviation of the underlying effects. For absolute measures, the random-effects
  estimate plus and minus 2×tau approximates a 95% range of true effects (centre
  on the log estimate for ratio measures, then exponentiate).

The most useful sentence in a heterogeneous synthesis is usually the one the
pooled estimate cannot produce: the random-effects confidence interval describes
uncertainty in the *mean* effect, not the spread of effects. Where no individual
study resembles the mean, report a **prediction interval** - the interval for
the effect in a new setting - and interpret that, not the pooled mean alone.

## Exploring heterogeneity

Subgroup analysis and meta-regression are observational comparisons, however
randomised the underlying trials. Two rules:

- **Pre-specify** the characteristics in the protocol, and keep the number
  small. Anything chosen after seeing the results is hypothesis-generating and
  must be labelled as such in the text, the abstract, and any conclusion.
- **Ten studies per characteristic** is the rough floor for meta-regression and
  it is not enough when the covariate is unevenly distributed. A *p* value from
  a subgroup comparison answers whether subgroups differ, not whether the
  intervention works in that subgroup - the latter is an observational claim
  inside a randomised trial.

Before searching for a cause, re-check the data. Severe heterogeneity is more
often a mis-extracted standard error, a denominator of attempts instead of
people, or a scale entered in the wrong units than a real difference in effect.

## Missing data and intention to treat

- Report how much is missing, by variable and by arm, and why. Differential
  missingness between arms is the version that biases the result.
- State the assumed mechanism - missing completely at random, at random, or not
  at random - because the analysis choice depends on it, and the assumption is
  usually untestable from the data.
- Last-observation-carried-forward and similar single-imputation approaches
  treat invented values as measurements, understate the variance, and are not a
  true intention-to-treat analysis. Where they were used, name them and test the
  result against a plausible worst-case or best-worst analysis.
- An intention-to-treat claim is a statement about how participants were
  analysed, not a compliment. Check the denominators before repeating it.

## Getting numbers out of a report

- A standard deviation can usually be derived from a standard error, a
  confidence interval, a *t* or *F* value, or a *p* value with the group size.
  Do the derivation and record it; do not assume the number was reported.
- **Interquartile range:** dividing by 1.35 approximates an SD only when the
  distribution is roughly normal. An IQR is often reported *because* the data
  are skewed, in which case the conversion is invalid and the outcome belongs in
  a narrative summary.
- **Range:** never use range/4 or similar. Ranges describe extremes, widen as
  sample size grows, and the conversion is not robust.
- **Median instead of mean:** usable when the distribution is close to
  symmetric; when it is not, say the study could not be pooled.
- Imputing an SD from other studies is a last resort. Name the source of the
  imputed value, the studies it was applied to, and check that the conclusion
  survives without them.
- **Combining subgroups** into one arm is legitimate using the standard pooled
  formulas for mean, SD and *n*; note that the simple pooled-SD approximation
  slightly underestimates the SD of the combined group.
- A quick skew check where a theoretical minimum or maximum exists: (mean −
  minimum)/SD < 2 suggests skew, < 1 is strong evidence of it. Not valid for
  change-from-baseline scores.
- Change scores and final values measure different things, and their SDs differ
  for reasons unrelated to the scale. Do not combine them as SMDs.

## Reporting biases

- Publication, selective-outcome, language, citation and multiple-publication
  bias are distinct mechanisms with one shared consequence: the studies you can
  find are not a random sample of the studies that were done.
- A funnel plot and its asymmetry tests need roughly **ten** studies before they
  can be interpreted - below that the tests have too little power to separate
  chance from real asymmetry, and the same applies when every study is of a
  similar size. Read the test alongside the plot, ask whether one study is
  producing the result, and note that asymmetry is also produced by genuine
  differences in effect between small and large studies. It is evidence of
  *small-study effects*, which publication bias is only one explanation of.
  Where the test is negative, bias is still not excluded: the test is weak, not
  exonerating.
- Trial registers and results databases are the antidote, not a supplement.
  Report the registrations you found with no corresponding publication - that
  list is a finding.
- Compare the protocol's primary outcome against the paper's. Outcome switching
  is common and is visible exactly at the point where the analysis plan was
  written.

## Presenting the result

Standard elements, in the order a reader needs them:

- **Forest plot** with the effect measure on the axis, individual studies with
  their confidence intervals, the pooled estimate as a diamond, and the
  heterogeneity statistics and the model named on the plot.
- **Summary of findings table** at the front of a review, one row per
  patient-important outcome, each row carrying: the outcome; the typical burden
  on the control (an illustrative risk or mean); the absolute and relative
  effect where both are meaningful; the number of participants and studies; the
  certainty rating for that outcome; and a comment. Certainty is rated **per
  outcome**, not per study and not per review.
- Outcomes are chosen before the analysis, from what patients and decision
  makers need - including harms and burden. Where the trials did not measure an
  important outcome, that absence goes in the table or the text, because a
  reader who does not see a row assumes the outcome was fine.

## Certainty of a body of evidence (GRADE)

Start randomised evidence at **high** and observational evidence at **low**, then
assess five factors that lower it and three that raise it. Downgrade one level
for a serious problem and two for a very serious one, up to three levels in
total.

Lower the rating for: limitations in design and implementation (the risk-of-bias
assessment, aggregated for the studies contributing to that outcome);
**indirectness** of population, intervention, comparator or outcome;
unexplained **inconsistency**; **imprecision** (wide confidence intervals, or an
interval that includes both a worthwhile benefit and a worthwhile harm); and
high probability of **publication bias**.

Raise the rating for observational evidence when there is a **large magnitude of
effect**, a **dose-response gradient**, or where **all plausible confounding
would reduce a demonstrated effect** or would produce a spurious effect when
none is seen. These are the three conditions under which an observational body
of evidence can be rated moderate or even high, and they are demanding.

Then make the language match the rating, because this is where health research
writing fails most often. The wording ladder - high certainty permits "reduces";
moderate permits "probably reduces"; low permits "may reduce"; very low permits
"the evidence is insufficient to determine whether it reduces" - is later GRADE
guidance rather than the 2008 Handbook text, but it follows directly from the
rating and it is now what readers expect. A low-certainty finding described with
a high-certainty verb is a wrong result, whatever the numbers say.

## Interpreting the numbers

- **Absolute before relative.** A risk ratio of 2 sounds large whether the risk
  goes from 1 in 10,000 to 2 in 10,000 or from 1 in 10 to 2 in 10. Natural
  frequencies - "70 fewer strokes per 1,000 patients over one year" - are better
  understood than percentages, and they force the baseline risk into view.
- **NNT is 1/|risk difference|**, rounded up, and it is a comparative property
  of this intervention against *that* comparator over a *stated* time frame - not
  a property of the intervention. Because it is derived from the risk
  difference, it changes with baseline risk: warfarin prevents about 70 strokes
  per 1,000 patient-years in high-risk atrial fibrillation and about 12 in
  low-risk patients, at the same relative effect. Where a meta-analysis pooled a
  relative measure, re-express it across a range of plausible control risks
  rather than quoting one NNT.
- Never compute an absolute risk reduction or NNT by totalling participants and
  events across trials; that ignores randomisation within each study.
- Say **NNTB** and **NNTH** (for an additional beneficial or harmful outcome)
  rather than "number needed to harm", which readers misread as a count of
  people who will be hurt.
- For continuous outcomes, report an SMD with its confidence interval and
  interpret it against a stated, outcome-specific anchor - the MID, or the
  smallest change a patient or clinician would notice - not against the
  0.2/0.5/0.8 conventions. Report the pooled mean difference instead where the
  studies used one scale.
- Where the pooled estimate is not interpretable at the level of a single
  patient (a risk ratio applied to an unstated baseline), say so and give the
  numbers a decision maker would need.
