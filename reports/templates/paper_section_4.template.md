# 4. Experimental results and discussion

**Authors:** Ernur Kussain and Zhanassyl Zhakyp

This section reports the results of the Task 3 analysis. Equation numbers refer to the domain model in [`docs/domain_model.md`](../docs/domain_model.md); tables and figures are numbered within this section. All values are generated from `reports/results.json` and `data/processed/` by `src/build_report.py`. In the tables, bold marks the better value only where one direction is better (model fit, latency); association statistics are not highlighted.

## 4.1 Setup

The main sample has $n = {{nMain}}$ bachelor's and master's respondents from the supplied cleaned workbook (Sharma et al., 2026). Two sensitivity samples are drawn from the raw workbook with our own rules: sensitivity A ($n = {{nA}}$) keeps academic GenAI users, and sensitivity B ($n = {{nB}}$) also keeps respondents who use GenAI rarely or never, coded as level 0. The exposure $x_i$ is the ordinal use frequency and the target $y_i$ is the six-item Unintentional Procrastination Scale total (Eq. 1). The primary metric is Spearman's coefficient

```math
\hat\rho_s = \operatorname{corr}\bigl(R(\mathbf{x}),\, R(\mathbf{y})\bigr), \qquad H_0:\ \rho_s = 0,
```

with a 95% percentile bootstrap interval over $B = 10\,000$ paired resamples (Eq. 4) and a permutation p-value (Eq. 6). The supplementary model compares the covariates-only baseline $M_0$ with the proposed model $M_1$, which adds $x_i$ (Eqs. 7 to 9). The pipeline benchmark times the Task 2 analysis on workloads of 50 to 2,000 records; latency percentiles exclude warm-up runs (Eqs. 15 and 16), and the speed-up is

```math
\mathcal{S}(w) = \frac{\mathrm{p}50_{\text{base},w}}{\mathrm{p}50_{\text{vec},w}} .
```

## 4.2 Primary association

**Table 1.** Association between academic GenAI-use frequency and UPS total. Intervals are 95% percentile bootstrap intervals; $H$ and $\varepsilon^2$ come from the Kruskal–Wallis test across use levels (Eq. 11).

{{TABLE_ASSOC}}

In the main sample $\hat\rho_s = {{rhoMain}}$ (95% CI {{rhoMainLo}} to {{rhoMainHi}}), and the interval excludes the null value. The permutation p-value is at its floor of $1/(B+1)$, so the asymptotic and resampling tests agree. Both raw-file analyses give estimates of similar size ($\hat\rho_s = {{rhoA}}$ and {{rhoB}}), so the authors' unexplained exclusions do not appear to drive the result. All bootstrap resamples were valid ($v = 1.00$), and the UPS items were internally consistent (Cronbach's $\alpha = {{alphaC}}$, Eq. 13).

![Figure 1](figures/fig2_distribution_boxplot.png)

**Figure 1.** Distribution of UPS totals (points, possible range 6 to 24) for each academic GenAI-use level in the main sample ($n = {{nMain}}$). Boxes span p25 to p75, the centre line is the median and whiskers reach 1.5 IQR; jittered points are individual respondents; black diamonds with error bars are medians with 95% bootstrap intervals (10,000 resamples). Scores rise from monthly to a-few-times-a-week use and level off for daily users.

## 4.3 Comparison with the lowest-use reference group

**Table 2.** UPS score by use level and comparison with the reference group (Median (p25–p75) and Mean ± SD in UPS points). The largest Cliff's δ in each sample is in bold.

{{TABLE_GROUPS}}

Respondents who use GenAI a few times a week or every day score 3 to 4 points higher than the monthly reference group and 4 to 5 points higher than the rarely/never group. Weekly users do not differ clearly from the monthly group. The effect sizes for the two highest levels ($\delta \approx 0.4$ to $0.5$) are medium to large by common conventions for Cliff's δ.

![Figure 2](figures/fig3_ups_vs_ai_frequency.png)

**Figure 2.** UPS score (points) across AI-use levels 0 to 4. Solid line with circles: main-sample medians; dashed line with open triangles: main-sample means; dotted line with squares: means in the raw five-level sample, which adds the rarely/never reference group at level 0. Error bars are 95% bootstrap intervals and the shaded band is the main-sample p25 to p75 range. The increase is steepest between levels 0 and 3.

## 4.4 Baseline versus proposed model

**Table 3.** Baseline model $M_0$ versus proposed model $M_1$, $n = {{nMain}}$. The better value of each criterion is in bold.

{{TABLE_MODELS}}

The covariates alone explain almost none of the variance ($R^2 = {{rTwoBase}}$). Adding AI-use frequency raises $R^2$ to {{rTwoProp}} ($\Delta R^2 = {{dRTwo}}$; nested $F = {{Fnested}}$, $p$ {{pNested}}). The coefficient is $\hat\beta = {{beta}}$ UPS points per frequency level (HC3 95% CI {{betaLo}} to {{betaHi}}), or $\beta_{\text{std}} = {{betaStd}}$ (95% CI {{betaStdLo}} to {{betaStdHi}}). Treating frequency as categorical gives a similar gain ($\Delta R^2 = {{catDRTwo}}$). Residuals are not normal (Shapiro–Wilk $p = {{shapiroP}}$), which is why HC3 errors are used; the Breusch–Pagan test does not indicate heteroscedasticity ($p = {{bpP}}$).

![Figure 3](figures/fig4_effect_size_forest.png)

**Figure 3.** Effect sizes with 95% intervals for the main analysis, both sensitivity analyses (Spearman ρ, percentile bootstrap) and the adjusted model (standardised β, HC3). The solid line is the null baseline $\rho_s = 0$ and the dashed line is the published β = 0.309 of Abbas et al. (2024), which used a different procrastination measure. All four intervals exclude zero and overlap one another.

## 4.5 Pipeline benchmark

**Table 4.** Latency per run in ms after warm-up filtering (successful runs only), with the p50 speed-up of the proposed implementation and its 95% bootstrap interval. The lower latency in each row is in bold.

{{TABLE_LATENCY}}

The log holds {{nLog}} timed runs; {{nWarm}} warm-up runs were discarded and {{nBench}} benchmark runs were analysed. They were collected on {{cpu}} with {{ncpu}} logical CPUs and Python {{pyBench}}. On identical inputs the two implementations returned the same estimates (largest absolute difference {{maxDiff}} over {{nPaired}} paired runs), and the vectorised version was faster at every workload: from {{speedMin}}× at {{speedMinN}} records to {{speedMax}}× at {{speedMaxN}} records. At the study's own sample size of 285 records the median run time fell from {{latBase}} ms to {{latVec}} ms ($\mathcal{S} = {{speedTwoEightFive}}$, 95% CI {{speedTwoEightFiveLo}} to {{speedTwoEightFiveHi}}).

**Table 5.** Guardrail metrics (Eqs. 14, 18 and 19).

{{TABLE_GUARDRAILS}}

All {{nInjected}} injected invalid batches were rejected by both implementations, and no unexpected error occurred.

![Figure 4](figures/fig1_latency_vs_load.png)

**Figure 4.** Pipeline latency per run (ms, log scale) against workload (records per run, log scale) for the Task 2 loop bootstrap (circles) and the vectorised bootstrap (squares). Solid, dashed and dotted lines are p50, p95 and p99; shaded bands are 95% bootstrap intervals of p50 and p95. Warm-up runs are excluded. The gap between the implementations narrows as the workload grows.

![Figure 5](figures/fig5_latency_distribution.png)

**Figure 5.** Latency distributions (ms, log scale) of the benchmark runs for each workload and implementation; boxes span p25 to p75 and whiskers 1.5 IQR, with outliers flagged but kept. Black crosses are the discarded warm-up runs. Cold runs were at most about 1.6 times the benchmark median, so the warm-up effect is small in this pipeline.

![Figure 6](figures/fig6_summary_panels.png)

**Figure 6.** Four-panel summary. (a) Median UPS score (points) per AI-use level in the main and five-level samples, with 95% bootstrap intervals. (b) Effect sizes (ρ or standardised β) with 95% intervals; the dashed line marks Abbas et al. (2024). (c) p50 and p95 latency (ms, log scale) against workload, with 95% bootstrap bands around p50. (d) p50 speed-up (×) of the vectorised implementation with 95% bootstrap intervals; the dotted line marks no speed-up.

## 4.6 Discussion

In this Indian sample, more frequent academic GenAI use goes with more unintentional procrastination. The size of the association ($\hat\rho_s = {{rhoMain}}$) is close to the 75th percentile of correlations in individual-differences research (Gignac & Szodorai, 2016) and within the range of 2024–2026 studies of GenAI use or dependence and procrastination (about 0.23 to 0.43; Abbas et al., 2024; Galindo-Domínguez et al., 2026; Liu & Liu, 2026). The standardised coefficient of {{betaStd}} is close to the β = 0.309 of Abbas et al. (2024).

The result is an association. The design is cross-sectional, and the strongest longitudinal evidence found so far points the other way: in a baseline-adjusted three-wave panel, GenAI-use frequency did not predict later procrastination (Zhao et al., 2026). The UPS correlates strongly with general procrastination and moderately with depression and anxiety (Fernie et al., 2017), so stable traits and distress, which the source data do not measure, may explain part of the association. Students who already procrastinate may also turn to GenAI more often.

For Kazakhstan no study yet measures GenAI use together with procrastination. GenAI use is already widespread among Kazakhstani students (65% weekly academic use in one 2024 survey of 840 students; Zhunusbekova & Askarkyzy, 2024), AI courses are compulsory, and universities set their own integrity rules. A frequency item may therefore vary less there and reflect course demands more than personal habit. Our result is best treated as a hypothesis for a Kazakhstani study that uses validated Kazakh and Russian versions of the UPS, measures the type of use and dependence as well as frequency, and follows students over several waves.

## References

Abbas, M., Jam, F. A., & Khan, T. I. (2024). Is it harmful or helpful? Examining the causes and consequences of generative AI usage among university students. *International Journal of Educational Technology in Higher Education, 21*, 10. https://doi.org/10.1186/s41239-024-00444-7

Fernie, B. A., Bharucha, Z., Nikčević, A. V., & Spada, M. M. (2017). The Unintentional Procrastination Scale. *Journal of Rational-Emotive & Cognitive-Behavior Therapy, 35*, 136–149. https://doi.org/10.1007/s10942-016-0247-x

Galindo-Domínguez, H., Sainz-de-la-Maza, M., Campo, L., & Losada-Iglesias, D. (2026). The influence of learning motivation and procrastination on ChatGPT dependence. *RIED-Revista Iberoamericana de Educación a Distancia, 29*(1), 217–240. https://doi.org/10.5944/ried.45497

Gignac, G. E., & Szodorai, E. T. (2016). Effect size guidelines for individual differences researchers. *Personality and Individual Differences, 102*, 74–78. https://doi.org/10.1016/j.paid.2016.06.069

Liu, Y., & Liu, Y. (2026). Association between perceived usefulness of generative AI for learning and generative AI dependency among university students in Changde, China. *Frontiers in Psychology, 17*, 1859317. https://doi.org/10.3389/fpsyg.2026.1859317

Sharma, P., Nandy, D., Ramchandani, G., James, A., Batra, M., & Dhanda, R. (2026). *Datasheets for Role of Generative Artificial Intelligence Usage on Academic Dishonesty Among Indian Undergraduate and Postgraduate Students* (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/88pv88j8jb.1

Zhao, Y., Chen, J., Dai, W., & Gu, Y. (2026). Learning-centred use of generative AI and later academic functioning: A baseline-adjusted three-wave panel study. *Frontiers in Psychology, 17*, 1878514. https://doi.org/10.3389/fpsyg.2026.1878514

Zhunusbekova, A., & Askarkyzy, S. (2024). Students' perceptions of artificial intelligence use in higher education and its impact on academic integrity. *Pedagogy and Psychology, 61*(4), 145–155. https://doi.org/10.51889/2960-1649.2024.61.4.008
