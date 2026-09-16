# Evidence appraisal

Appraisal asks two separate questions: is this study any good, and does this
collection of studies contain the number of independent pieces of evidence it
appears to.

## What each design can support

| Design | Supports | Does not support |
|---|---|---|
| Randomised trial | Causal effect of the intervention as delivered, in the population randomised | Effect in populations not represented; mechanism |
| Cluster or stepped-wedge trial | Effect where randomising individuals is impossible | Individual-level effect sizes without accounting for clustering |
| Quasi-experimental (difference-in-differences, interrupted time series) | Plausible causal effect when a contemporaneous comparison exists | Causal claims where the parallel-trends assumption fails and is untested |
| Cohort | Association and prognosis | Causation, without strong design support |
| Case-control | Association for rare outcomes | Incidence, absolute risk |
| Cross-sectional | Prevalence and association | Anything temporal |
| Qualitative | Mechanism, experience, why an intervention failed | Frequency, effect size |
| Decision model | Cost-effectiveness under stated assumptions | Anything its inputs do not support |

Never pool across designs without saying which estimate is doing the work.

## Risk of bias

Use the instrument matched to the design rather than inventing criteria: Cochrane
RoB 2 for randomised trials, ROBINS-I for non-randomised intervention studies,
Newcastle-Ottawa for cohort and case-control, and the JBI checklists for
prevalence, qualitative and economic studies.

Judge the study, not the paper. A well-written discussion does not reduce the
risk of bias in the estimate.

The instruments are checklists of the same underlying questions, so knowing what
they are asking lets you read an assessment rather than trust its summary
judgement. The original Cochrane tool (Handbook v5.0.1, 2008) had six domains,
and each is still the place a trial's estimate is lost:

- **Sequence generation** - a random component, or a rule (date of birth,
  admission day, record number, clinician's judgement) that participants and
  staff can work out.
- **Allocation concealment** - could the person enrolling the next participant
  have foreseen the assignment? Central or pharmacy randomisation, or
  sequentially numbered opaque sealed envelopes, count. Open random-number
  lists, unsealed or unnumbered envelopes, alternation and rotation do not.
- **Blinding** of participants, personnel and outcome assessors - and for which
  outcomes. Lack of blinding matters most for subjective outcomes and hardly at
  all for all-cause mortality, so an assessment is per outcome, not per trial.
- **Incomplete outcome data** - how much, whether it is balanced between arms,
  and what the analysis did about it.
- **Selective reporting** - compare the protocol or registration against the
  paper's outcomes.
- **Other sources** - anything the other five do not capture, named specifically
  rather than as a general concern.

Each domain is judged low, high or unclear risk. "Unclear" is not a neutral
verdict: it means the report does not say, and where the assessment informs a
pooled estimate it counts as a limitation. The current tools (RoB 2 for trials,
ROBINS-I for non-randomised studies) restructured these domains and moved the
judgement from the study to the **result** for each outcome, which is the trend
worth following even where a protocol was written under the older tool.

Where the primary analysis is restricted to studies at low risk of bias, say so
and show what the unrestricted analysis would have given. Restricting it is a
defensible choice; restricting it silently is not.

## Independence: counting studies, not papers

This is the check most often skipped, and the one that most changes conclusions.
The literature routinely contains several papers describing a single study.

Signals that entries may be one study, not several:

- the same trial registration identifier (NCT, ISRCTN, ACTRN, ChiCTR, ANZCTR)
- the same sample size and the same recruitment period
- a shared baseline characteristics table
- the same cohort followed to different follow-up points
- a secondary or cost-effectiveness analysis of an effectiveness trial
- overlapping author groups publishing in quick succession
- the same funder, site and protocol

When two or more entries share a study, count them once in any tally of evidence,
cite the primary report for the effect and the companion paper only for what it
uniquely adds - usually costs, a subgroup, or longer follow-up.

Say so explicitly: "six reports, four studies" is a finding, and it belongs in
the text. Presenting six reports as six studies overstates certainty just as
plainly as fabricating a study, and it is far harder for a reader to spot.

## Effect measures

- Report effect sizes with confidence intervals. A p-value alone tells the reader
  nothing about magnitude.
- Relative and absolute measures answer different questions. A halved risk from
  2 in 1,000 to 1 in 1,000 is a large ratio and a trivial absolute difference.
  Give both where the outcome is rare.
- Standardised mean differences are comparable across studies only when the
  underlying constructs are comparable. An SMD on one instrument is not
  interchangeable with an SMD on another, and the rules of thumb that treat 0.2,
  0.5 and 0.8 as small, moderate and large are conventions, not measurements.
- Time-to-event hazard ratios assume proportional hazards. Where the curves
  cross, or the assumption is untested, the ratio is misleading and the
  difference in restricted mean survival time is more honest.

## Heterogeneity and pooling

Ask first whether pooling is clinically meaningful. Studies with different
comparators, different outcome definitions, different settings or different
follow-up durations may not share a common effect to estimate.

Statistical heterogeneity - I-squared, tau-squared - tells you about consistency,
not about whether pooling was sensible. High heterogeneity with a reported pooled
estimate is a signal to look at the individual studies rather than to discount
them.

Prefer a random-effects model where effects genuinely differ, and say why you
chose it. Report whether a fixed-effect analysis would have changed the
conclusion, because if it would, the conclusion depends on the model choice.

Before running any of this, read `synthesis-and-meta-analysis.md`: it covers the
unit-of-analysis errors that make a pooled confidence interval too narrow, the
mistake of choosing the model on the basis of a heterogeneity test, prediction
intervals, and how to report a pooled result so that a reader can see what it is
the average of.

## Publication and reporting bias

- Small studies with null results are less likely to be published. A funnel plot
  with few studies cannot distinguish this from chance, and asymmetry tests need
  roughly ten studies before they mean anything.
- Registered trials with no published results are a finding in themselves. Check
  the registry, and say which registrations had no corresponding publication.
- Outcome switching between protocol and paper is common. Where you can see the
  protocol, compare the primary outcome.

## Certainty

Grade the body of evidence, not each study in isolation: GRADE for
intervention questions, and an explicit narrative scheme for others.

Then use language that matches the grade. High certainty permits "reduces";
low certainty permits "may reduce"; very low certainty permits "the evidence is
insufficient to determine". Most errors of tone in health research writing are a
low-certainty finding described with high-certainty verbs.
