# Measurement

A scale score is an estimate produced by an instrument, not a property of the
person. Before a score is used to compare groups, track change, or name a
subgroup, the instrument has to be shown to behave well enough to carry that
weight - in this population, in this language, at this timepoint.

## Reliability

- **Internal consistency.** Cronbach's alpha is the convention, and it is not a
  measure of unidimensionality: a two-factor scale can produce a high alpha.
  Where items are not equally related to the construct, McDonald's omega is the
  better estimate. Never report alpha as evidence of a single underlying factor.
- **Test-retest.** Report the intraclass correlation with the form used
  (absolute agreement versus consistency) and its confidence interval. State the
  interval between administrations; too short measures memory, too long measures
  change.
- **Inter-rater agreement.** Weighted kappa for ordinal ratings, ICC for
  continuous. Kappa falls as the trait becomes rare or very common, so report
  prevalence and consider a prevalence-adjusted statistic rather than concluding
  poor agreement from a low kappa alone.
- **Minimal detectable change.** Reliability without the smallest change that
  exceeds measurement error leaves a reader unable to judge whether a difference
  means anything.

## Validity

- **Structural.** Exploratory factor analysis where the structure is unknown in
  this population; confirmatory where a structure is being tested. Report the
  estimator, rotation, and the fit indices together - CFI, TLI, RMSEA, SRMR - and
  treat published cut-offs as conventions rather than pass marks.
- **Ordinal items.** Likert responses are ordinal. Pearson correlations and
  maximum-likelihood estimation assume they are continuous and can misstate the
  factor structure, particularly with fewer than five response options.
- **Convergent and discriminant.** Average variance extracted and the
  heterotrait-monotrait ratio are more informative than the older
  Fornell-Larcker comparison, which passes too easily.
- **Known-groups.** Does the instrument distinguish groups it should
  distinguish? This is often the most persuasive evidence and the least often
  reported.

## Measurement invariance

This is the check that decides whether a group comparison is interpretable at
all, and it matters especially in multi-ethnic Singapore samples.

Test in order: **configural** (same items load on the same factors), **metric**
(loadings equal), **scalar** (loadings and intercepts equal), **strict** (plus
residual variances). Each level licenses a different claim:

- scalar invariance is required before comparing **means**
- metric invariance is enough to compare **relationships** between constructs
- failing configural means the construct is not the same construct across groups

Where full invariance fails, partial invariance with the freed parameters named
is acceptable and must be reported as such. Reporting a group mean difference
without having tested invariance is the most common version of this error, and it
is invisible in the results table.

A scale validated in one population is not thereby validated in another. Where an
instrument has been translated, report forward and back translation, cognitive
interviews with members of the target population, and any item that was adapted.

## Latent classes and profiles

Latent class and latent profile analysis name subgroups, and the naming is where
the trouble starts. The classes are model-derived groups, not natural kinds, and
they are defined by conditional independence assumptions that real data often
violate.

Report class enumeration properly:

- fit statistics together, not selectively - BIC, sample-size-adjusted BIC,
  entropy, and the likelihood ratio tests; they routinely disagree, and the
  disagreement is part of the result
- class sizes, because a class of 3 percent of the sample is unlikely to
  replicate and should not anchor an interpretation
- the classification quality, so a reader can see how confidently cases were
  assigned
- whether the solution holds when the seed, the estimator, or the indicator set
  changes
- the indicators used, and why those

Name classes by their empirical profile, not by a construct the analysis did not
measure. "High-burden, low-self-efficacy" describes what was found;
"resigned carers" asserts something the data does not contain.

## Composite scores

State whether a score is a sum or a mean, and the scoring algorithm, because the
two are not interchangeable when items are missing. Person-mean imputation - the
common practice of averaging the items a respondent answered - biases scores
toward the middle and inflates precision; report how many respondents needed it.

Do not sum items that were measured on different scales, and do not compare
composites across instruments unless the construct and the metric are genuinely
the same.

## Reporting your own measure

For every instrument, state the version, the language, the scoring rule, the
source, and the licence or permission under which it was used. Several
caregiver-burden and quality-of-life instruments are copyrighted and require
registration or a fee, and a journal may ask for evidence of permission.

Finally, report the uncertainty in your own scores. A mean with a confidence
interval spanning a clinically meaningful difference supports a weaker claim than
the point estimate suggests.
