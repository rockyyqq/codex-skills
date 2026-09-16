# Economic evaluation

Health economics has its own failure modes, and most of them are invisible in the
final number. A cost per QALY is meaningless without the perspective, horizon,
price year and currency that produced it.

## Before any cost figure

Establish, and write down, four things. If any is missing, the number is not
usable and the honest answer is to ask for it.

1. **Perspective** - societal, healthcare payer, provider, patient or employer.
   Direct healthcare costs, patient time, informal caregiver time and
   productivity losses belong to different perspectives. A cost computed
   societally and reported as a payer cost is a category error.
2. **Time horizon** - long enough to capture the relevant costs and
   consequences. A one-year horizon on a chronic disease forces recurrence to
   zero by construction.
3. **Discount rate**, applied to both costs and outcomes, and whether outcomes
   were discounted at all. Discounting costs while leaving outcomes undiscounted
   flatters the intervention.
4. **Price year, currency, and whether the figure is inflated or converted to a
   common year.** Costs from different price years are not comparable, and adding
   them is a straightforward arithmetic error that survives review surprisingly
   often.

## Types, and the outcome each uses

| Type | Outcome | Use when |
|---|---|---|
| Cost analysis | None - costs only | Comparing the cost of alternatives with equivalent outcomes |
| Cost-minimisation | Assumed equivalent | Equivalence is demonstrated, not assumed for convenience |
| Cost-effectiveness | Natural units (cases averted, life-years) | A single dominant outcome matters |
| Cost-utility | QALYs or DALYs | Comparing across diseases, or when quality of life is affected |
| Cost-benefit | Money | Outcomes can be credibly monetised |
| Cost-consequence | Disaggregated list | No single summary measure is defensible |

The choice of outcome measure determines what comparisons the result can support.
A cost per case averted cannot be compared with a cost per QALY threshold.

## QALYs

A QALY combines length and quality of life: time in a health state multiplied by
a utility weight where 1 is full health and 0 is death. States worse than death
take negative weights, and whether the analysis allows those changes the result.

Verify which instrument produced the utilities - EQ-5D, SF-6D, HUI, AQoL - and
which value set. Utilities from different instruments are not interchangeable,
and the same instrument scored with different national value sets gives different
answers. Check whether utilities came from the study population or from the
literature, because the two answer different questions.

## Transferability between health systems

A cost-effectiveness ratio does not travel. Unit costs, clinical practice,
capacity, incentives and the comparator all differ between systems.

Where you must use evidence from elsewhere:

- separate the resource quantities (which travel better) from the unit costs
  (which do not), and reprice the quantities locally
- state the source of each local unit cost and its price year
- test the result against local cost assumptions, not just the original ones
- treat a transferred ratio as a hypothesis about your setting, not an estimate
  for it

Checklist-style frameworks exist for this; the point of them is transparency about
what was changed, not a score.

## Model structure

State the model type and justify it. A decision tree suits one-off events; a
Markov cohort model suits repeated transitions between health states; a discrete
event simulation or microsimulation is needed where history matters, where
individual trajectories matter, or where the population is heterogeneous in a way
that changes the result.

Things to check in any model you are reading or building:

- phase-specific or state-specific costs align with the states people actually
  occupy
- cycle length is short enough not to miss transitions, and any half-cycle
  correction is stated
- the comparator is the relevant current practice, not the cheapest or the most
  convenient
- the model horizon matches the clinical reality of the condition
- structural assumptions are listed, not buried in a supplement

## Uncertainty

Three distinct things, often conflated:

- **Parameter uncertainty** - one-way sensitivity analysis and tornado diagrams
  show which inputs matter; probabilistic sensitivity analysis propagates all of
  them together.
- **Structural uncertainty** - different model structures or assumptions. Cannot
  be addressed by PSA, and is usually more consequential.
- **Heterogeneity** - real differences between patients, which subgroup analysis
  addresses rather than sensitivity analysis.

Report the cost-effectiveness acceptability curve, and the probability that the
intervention is cost-effective at the relevant threshold. A single ICER with no
interval implies a precision the estimate does not have.

Discount the value of perfect information appropriately: it belongs where it would
change a decision, not appended as a formality.

## Common errors worth checking for by name

- inconsistent perspective, where costs from one viewpoint are combined with
  outcomes framed in another
- mixing price years, or failing to state the price year at all
- double counting, especially where informal care appears as both a cost and a
  productivity loss
- indirect costs included under a payer perspective
- discounting costs but not outcomes
- a time horizon too short for the disease
- extrapolating trial effects beyond the trial duration without saying so
- the comparator omitted entirely, so the intervention is compared with nothing
- conclusions stated without the threshold that makes them meaningful

## Thresholds

A willingness-to-pay threshold is a policy choice, not a scientific constant. Where
a threshold is used, name it and its source. Where a jurisdiction has no single
official threshold, say that - and do not import another country's.
