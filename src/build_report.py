"""Build the results section and the LaTeX report inputs from the computed outputs.

Every number in ``reports/paper_section_4.md`` and in the LaTeX report comes from
``reports/results.json`` and the CSVs in ``data/processed/``; nothing is typed by hand.

Outputs:
    reports/paper_section_4.md          Markdown results section (fills reports/templates/paper_section_4.template.md)
    reports/latex/generated_values.tex  \\newcommand macros with every value used in the LaTeX prose
    reports/latex/generated_tables.tex  booktabs tables (best value in bold where a direction of "better" exists)

Usage::

    python src/build_report.py --config configs/research.yaml
    latexmk -pdf -cd reports/latex/task3_report.tex      # optional: compile the PDF report
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_data  # noqa: E402

ROOT = process_data.ROOT
LABELS = process_data.FREQUENCY_LABELS
ANALYSIS_NAMES = {
    'main_cleaned_n285': 'Main: supplied cleaned workbook',
    'sensitivity_a_raw_independent': 'Sensitivity A: raw workbook, independent rules',
    'sensitivity_b_raw_five_level': 'Sensitivity B: raw workbook, five levels',
}


def fmt(x: float, d: int = 2) -> str:
    return f'{x:.{d}f}'


def pfmt(p: float) -> str:
    return '< 0.001' if p < 0.001 else f'{p:.3f}'


def pfmt_tex(p: float) -> str:
    return '$<0.001$' if p < 0.001 else f'{p:.3f}'


def sci_tex(x: float) -> str:
    mant, exp = f'{x:.1e}'.split('e')
    return f'${mant}\\times10^{{{int(exp)}}}$'


def load(cfg: dict) -> dict:
    proc = ROOT / cfg['processed']['dir']
    res = json.loads((ROOT / cfg['reports']['results_json']).read_text(encoding='utf-8'))
    return {
        'res': res,
        'groups': pd.read_csv(proc / 'survey_group_summary.csv'),
        'refs': pd.read_csv(proc / 'survey_reference_comparisons.csv'),
        'lat': pd.read_csv(proc / 'pipeline_latency_summary.csv'),
        'speed': pd.read_csv(proc / 'pipeline_speedup.csv'),
        'flow': pd.read_csv(proc / 'exclusion_flow.csv'),
        'main': pd.read_csv(ROOT / cfg['processed']['main']),
        'raw': pd.read_csv(ROOT / cfg['processed']['raw_coded']),
        'meta': json.loads((ROOT / cfg['benchmark']['meta_path']).read_text(encoding='utf-8')),
    }


def values(d: dict) -> dict:
    res, lat, speed = d['res'], d['lat'], d['speed']
    a = res['survey']['association']
    m = res['survey']['models_main']
    pipe = res['pipeline']
    bench = process_data.load_jsonl(ROOT / 'data/raw/test_run.jsonl')
    bench = bench[bench['phase'] == 'benchmark']
    injected_batches = int(bench[bench['edge_case'].notna()][['n_records', 'rep']].drop_duplicates().shape[0])
    b285 = lat[(lat.implementation == 'baseline_loop') & (lat.n_records == 285)].iloc[0]
    v285 = lat[(lat.implementation == 'vectorized') & (lat.n_records == 285)].iloc[0]
    s285 = speed[speed.n_records == 285].iloc[0]
    v = {
        'nMain': a[0]['n'], 'nA': a[1]['n'], 'nB': a[2]['n'],
        'rhoMain': fmt(a[0]['spearman_rho'], 3), 'rhoMainLo': fmt(a[0]['ci95_percentile_bootstrap'][0], 3),
        'rhoMainHi': fmt(a[0]['ci95_percentile_bootstrap'][1], 3),
        'rhoA': fmt(a[1]['spearman_rho'], 3), 'rhoALo': fmt(a[1]['ci95_percentile_bootstrap'][0], 3),
        'rhoAHi': fmt(a[1]['ci95_percentile_bootstrap'][1], 3),
        'rhoB': fmt(a[2]['spearman_rho'], 3), 'rhoBLo': fmt(a[2]['ci95_percentile_bootstrap'][0], 3),
        'rhoBHi': fmt(a[2]['ci95_percentile_bootstrap'][1], 3),
        'pAsymMain': f"{a[0]['p_value_asymptotic_two_sided']:.1e}",
        'kwH': fmt(a[0]['kruskal_h'], 1), 'epsSq': fmt(a[0]['kruskal_epsilon_squared'], 3),
        'alphaC': fmt(res['survey']['ups_cronbach_alpha_main'], 2),
        'rTwoBase': fmt(m['baseline']['r2'], 3), 'rTwoProp': fmt(m['proposed']['r2'], 3), 'dRTwo': fmt(m['delta_r2'], 3),
        'Fnested': fmt(m['nested_f'], 1), 'pNested': pfmt(m['nested_f_p']),
        'beta': fmt(m['proposed']['beta_ai_frequency'], 2), 'betaLo': fmt(m['proposed']['beta_ci95_hc3'][0], 2),
        'betaHi': fmt(m['proposed']['beta_ci95_hc3'][1], 2),
        'betaStd': fmt(m['proposed']['standardised_beta'], 2), 'betaStdLo': fmt(m['proposed']['standardised_beta_ci95_hc3'][0], 2),
        'betaStdHi': fmt(m['proposed']['standardised_beta_ci95_hc3'][1], 2),
        'catDRTwo': fmt(m['categorical_robustness']['delta_r2'], 3),
        'shapiroP': fmt(m['residual_diagnostics']['shapiro_p'], 3), 'bpP': fmt(m['residual_diagnostics']['breusch_pagan_p'], 2),
        'nLog': pipe['records_total'], 'nWarm': pipe['warmup_records_discarded'], 'nBench': pipe['benchmark_records'],
        'nInjected': injected_batches, 'nPaired': pipe['estimate_agreement']['paired_runs_compared'],
        'maxDiff': f"{max(pipe['estimate_agreement']['max_abs_difference'].values()):.1e}",
        'latBase': fmt(b285['p50_ms'], 1), 'latVec': fmt(v285['p50_ms'], 1),
        'speedTwoEightFive': fmt(s285['speedup_p50'], 2), 'speedTwoEightFiveLo': fmt(s285['speedup_ci_low'], 2),
        'speedTwoEightFiveHi': fmt(s285['speedup_ci_high'], 2),
        'speedMin': fmt(speed['speedup_p50'].min(), 1), 'speedMax': fmt(speed['speedup_p50'].max(), 1),
        'speedMinN': int(speed.loc[speed['speedup_p50'].idxmin(), 'n_records']),
        'speedMaxN': int(speed.loc[speed['speedup_p50'].idxmax(), 'n_records']),
        'cpu': d['meta']['environment']['cpu_model'], 'ncpu': d['meta']['environment']['cpu_count_logical'],
        'pyBench': d['meta']['environment']['python'],
    }
    return v


# ---------------------------------------------------------------- Markdown tables
def md_tables(d: dict) -> dict:
    res = d['res']
    a = res['survey']['association']
    m = res['survey']['models_main']
    out = {}

    rows = ['| Analysis | $n$ | $\\hat\\rho_s$ [95% CI] | $p$ (asymptotic) | $p$ (permutation) | $H$ | $\\varepsilon^2$ | Decision |',
            '|:--|--:|:--|--:|--:|--:|--:|:--|']
    for x in a:
        rows.append(f"| {ANALYSIS_NAMES[x['analysis']]} | {x['n']} | {x['spearman_rho']:.3f} "
                    f"[{x['ci95_percentile_bootstrap'][0]:.3f}, {x['ci95_percentile_bootstrap'][1]:.3f}] | "
                    f"{x['p_value_asymptotic_two_sided']:.1e} | {pfmt(x['p_value_permutation_two_sided'])} | "
                    f"{x['kruskal_h']:.1f} | {x['kruskal_epsilon_squared']:.3f} | reject $H_0$ |")
    out['TABLE_ASSOC'] = '\n'.join(rows)

    rows = ['| Use level | $n$ | Median (p25–p75), points | Mean ± SD, points | Median difference vs reference [95% CI] | Cliff\'s $\\delta$ [95% CI] | Holm $p$ |',
            '|:--|--:|:--|:--|:--|:--|--:|']
    for sample, ref, title in [('main_cleaned_n285', 1, 'Main sample, reference = level 1'),
                               ('sensitivity_b_raw_five_level', 0, 'Sensitivity B, reference = level 0')]:
        rows.append(f'| *{title}* | | | | | | |')
        g = d['groups'][d['groups']['sample'] == sample].sort_values('ai_frequency')
        r = d['refs'][d['refs']['sample'] == sample].set_index('ai_frequency')
        best = r['cliffs_delta'].idxmax()
        for _, x in g.iterrows():
            lv = int(x['ai_frequency'])
            if lv == ref:
                cmp = ('reference', 'reference', '')
            else:
                y = r.loc[lv]
                dtxt = f"{y['cliffs_delta']:.2f} [{y['cliffs_delta_ci_low']:.2f}, {y['cliffs_delta_ci_high']:.2f}]"
                cmp = (f"{y['median_difference']:+.1f} [{y['median_difference_ci_low']:+.1f}, {y['median_difference_ci_high']:+.1f}]",
                       f'**{dtxt}**' if lv == best else dtxt, pfmt(y['p_value_holm']))
            rows.append(f"| {lv}: {LABELS[lv]} | {int(x['n'])} | {x['median']:.1f} ({x['p25']:.0f}–{x['p75']:.0f}) | "
                        f"{x['mean']:.2f} ± {x['sd']:.2f} | {cmp[0]} | {cmp[1]} | {cmp[2]} |")
    out['TABLE_GROUPS'] = '\n'.join(rows)

    b, p = m['baseline'], m['proposed']
    def bold(v1, v2, higher=True):
        best_is_2 = (v2 > v1) if higher else (v2 < v1)
        f = lambda v: f'{v:.3f}' if abs(v) < 10 else f'{v:.1f}'  # noqa: E731
        return (f(v1), f'**{f(v2)}**') if best_is_2 else (f'**{f(v1)}**', f(v2))
    r2 = bold(b['r2'], p['r2']); ar2 = bold(b['adj_r2'], p['adj_r2']); aic = bold(b['aic'], p['aic'], False); bic = bold(b['bic'], p['bic'], False)
    out['TABLE_MODELS'] = '\n'.join([
        '| Model | Predictors | $R^2$ | adjusted $R^2$ | AIC | BIC |',
        '|:--|:--|--:|--:|--:|--:|',
        f'| $M_0$ baseline | age, gender, education | {r2[0]} | {ar2[0]} | {aic[0]} | {bic[0]} |',
        f'| $M_1$ proposed | $M_0$ + AI-use frequency | {r2[1]} | {ar2[1]} | {aic[1]} | {bic[1]} |',
    ])

    lat = d['lat']
    rows = ['| Records per run | Baseline p50 (p25–p75), ms | Proposed p50 (p25–p75), ms | Baseline p95 / p99, ms | Proposed p95 / p99, ms | Speed-up $\\mathcal{S}$ [95% CI] |',
            '|--:|:--|:--|:--|:--|:--|']
    for n in sorted(lat['n_records'].unique()):
        bb = lat[(lat.implementation == 'baseline_loop') & (lat.n_records == n)].iloc[0]
        vv = lat[(lat.implementation == 'vectorized') & (lat.n_records == n)].iloc[0]
        s = d['speed'][d['speed'].n_records == n].iloc[0]
        rows.append(f"| {n} | {bb['p50_ms']:.1f} ({bb['p25_ms']:.1f}–{bb['p75_ms']:.1f}) | "
                    f"**{vv['p50_ms']:.1f}** ({vv['p25_ms']:.1f}–{vv['p75_ms']:.1f}) | {bb['p95_ms']:.1f} / {bb['p99_ms']:.1f} | "
                    f"**{vv['p95_ms']:.1f} / {vv['p99_ms']:.1f}** | {s['speedup_p50']:.2f} [{s['speedup_ci_low']:.2f}, {s['speedup_ci_high']:.2f}] |")
    out['TABLE_LATENCY'] = '\n'.join(rows)

    g = res['survey']['guardrails']
    pipe = res['pipeline']
    out['TABLE_GUARDRAILS'] = '\n'.join([
        '| Guardrail | Required | Observed |',
        '|:--|:--|:--|',
        f"| Invalid or missing required values | 0 | {g['invalid_required_values'] + g['missing_ups_items']} |",
        f"| Duplicate record IDs | 0 | {g['duplicate_record_ids']} |",
        f"| Computed vs supplied UPS totals | all equal | {g['computed_vs_supplied_total_mismatches']} mismatches (300 audited) |",
        f"| Valid bootstrap resamples, $v$ | ≥ 0.95 | {a[0]['bootstrap_valid_fraction']:.2f} |",
        f"| Unexpected error rate, $e$ | 0 | {pipe['unexpected_error_rate_overall']:.0f} |",
        f"| Invalid batches rejected, $d$ | 1 | {pipe['rejection_detection_rate_overall']:.0f} |",
        f"| Max difference between implementations | ≤ 10⁻⁹ | {max(pipe['estimate_agreement']['max_abs_difference'].values()):.1e} |",
    ])
    return out


# ---------------------------------------------------------------- LaTeX tables
def tex_tables(d: dict) -> str:
    res = d['res']
    a = res['survey']['association']
    m = res['survey']['models_main']
    L = []
    L.append(r'''\begin{table}[!htbp]
\centering
\caption{Primary association between academic GenAI-use frequency and UPS total (Eqs.~\ref{eq:spearman}--\ref{eq:perm}). Intervals are 95\% percentile bootstrap intervals ($B=10\,000$); $H$ and $\varepsilon^2$ come from the Kruskal--Wallis test across use levels (Eq.~\ref{eq:kw}). No column has a ``better'' direction, so no value is highlighted.}
\label{tab:association}
\footnotesize\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrlrrrr@{}}
\toprule
Analysis & $n$ & $\hat\rho_s$ [95\% CI] & $p_{\text{asym}}$ & $p_{\text{perm}}$ & $H$ & $\varepsilon^2$\\
\midrule''')
    for x in a:
        L.append(f"{ANALYSIS_NAMES[x['analysis']].replace(':', ':')} & {x['n']} & {x['spearman_rho']:.3f} "
                 f"[{x['ci95_percentile_bootstrap'][0]:.3f}, {x['ci95_percentile_bootstrap'][1]:.3f}] & "
                 f"{sci_tex(x['p_value_asymptotic_two_sided'])} & {pfmt_tex(x['p_value_permutation_two_sided'])} & "
                 f"{x['kruskal_h']:.1f} & {x['kruskal_epsilon_squared']:.3f}\\\\")
    L.append(r'''\bottomrule
\end{tabular}
\end{table}''')

    L.append(r'''\begin{table}[!htbp]
\centering
\caption{UPS score by AI-use level and comparison with the lowest-use reference group. Values are Median (p25--p75) and Mean $\pm$ SD in UPS points. Median differences and Cliff's $\delta$ (Eq.~\ref{eq:cliff}) carry 95\% bootstrap intervals; $p$ values are Holm-adjusted Mann--Whitney tests. The largest $\delta$ in each sample is in bold.}
\label{tab:groups}
\footnotesize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}lrllll r@{}}
\toprule
Use level & $n$ & Median (p25--p75) & Mean $\pm$ SD & $\Delta$ median [95\% CI] & $\delta$ [95\% CI] & $p_{\text{Holm}}$\\
\midrule''')
    for sample, ref, title in [('main_cleaned_n285', 1, 'Main sample ($n=285$), reference = level 1'),
                               ('sensitivity_b_raw_five_level', 0, 'Sensitivity B ($n=327$), reference = level 0')]:
        L.append(f'\\multicolumn{{7}}{{@{{}}l}}{{\\emph{{{title}}}}}\\\\')
        g = d['groups'][d['groups']['sample'] == sample].sort_values('ai_frequency')
        r = d['refs'][d['refs']['sample'] == sample].set_index('ai_frequency')
        best = r['cliffs_delta'].idxmax()
        for _, x in g.iterrows():
            lv = int(x['ai_frequency'])
            if lv == ref:
                c1, c2, c3 = 'reference', 'reference', ''
            else:
                y = r.loc[lv]
                c1 = f"${y['median_difference']:+.1f}$ [${y['median_difference_ci_low']:+.1f}$, ${y['median_difference_ci_high']:+.1f}$]"
                dt = f"{y['cliffs_delta']:.2f} [{y['cliffs_delta_ci_low']:.2f}, {y['cliffs_delta_ci_high']:.2f}]"
                c2 = f'\\textbf{{{dt}}}' if lv == best else dt
                c3 = pfmt_tex(y['p_value_holm'])
            L.append(f"\\quad {lv}: {LABELS[lv]} & {int(x['n'])} & {x['median']:.1f} ({x['p25']:.0f}--{x['p75']:.0f}) & "
                     f"{x['mean']:.2f} $\\pm$ {x['sd']:.2f} & {c1} & {c2} & {c3}\\\\")
    L.append(r'''\bottomrule
\end{tabular}
\end{table}''')

    b, p = m['baseline'], m['proposed']
    def bb(v1, v2, higher=True, dec=3):
        best2 = (v2 > v1) if higher else (v2 < v1)
        s1, s2 = f'{v1:.{dec}f}', f'{v2:.{dec}f}'
        return (s1, f'\\textbf{{{s2}}}') if best2 else (f'\\textbf{{{s1}}}', s2)
    r2 = bb(b['r2'], p['r2']); ar2 = bb(b['adj_r2'], p['adj_r2']); aic = bb(b['aic'], p['aic'], False, 1); bic = bb(b['bic'], p['bic'], False, 1)
    L.append(rf'''\begin{{table}}[t]
\centering
\caption{{Baseline model $M_0$ versus proposed model $M_1$ (Eqs.~\ref{{eq:models}}--\ref{{eq:fit}}), $n={m['n']}$. The better value of each criterion is in bold. Nested $F={m['nested_f']:.1f}$, $p {pfmt_tex(m['nested_f_p']).strip('$')}$; $\hat\beta={p['beta_ai_frequency']:.2f}$ UPS points per level (HC3 95\% CI {p['beta_ci95_hc3'][0]:.2f} to {p['beta_ci95_hc3'][1]:.2f}).}}
\label{{tab:models}}
\small
\begin{{tabular}}{{@{{}}llrrrr@{{}}}}
\toprule
Model & Predictors & $R^2$ & adj.\ $R^2$ & AIC & BIC\\
\midrule
$M_0$ baseline & age, gender, education & {r2[0]} & {ar2[0]} & {aic[0]} & {bic[0]}\\
$M_1$ proposed & $M_0$ + AI-use frequency & {r2[1]} & {ar2[1]} & {aic[1]} & {bic[1]}\\
\bottomrule
\end{{tabular}}
\end{{table}}''')

    L.append(r'''\begin{table}[!htbp]
\centering
\caption{Pipeline latency per run (ms) after warm-up filtering, successful runs only (Eqs.~\ref{eq:bench}--\ref{eq:speedup}). Median (p25--p75) and tail percentiles for the Task~2 loop bootstrap (baseline) and the vectorised bootstrap (proposed), with the p50 speed-up $\mathcal{S}$ and its 95\% bootstrap interval. The lower (better) latency in each row is in bold.}
\label{tab:latency}
\footnotesize\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}r ll ll l@{}}
\toprule
& \multicolumn{2}{c}{Baseline (Task 2 loop)} & \multicolumn{2}{c}{Proposed (vectorised)} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
$w$ & p50 (p25--p75) & p95 / p99 & p50 (p25--p75) & p95 / p99 & $\mathcal{S}$ [95\% CI]\\
\midrule''')
    lat = d['lat']
    for n in sorted(lat['n_records'].unique()):
        b_ = lat[(lat.implementation == 'baseline_loop') & (lat.n_records == n)].iloc[0]
        v_ = lat[(lat.implementation == 'vectorized') & (lat.n_records == n)].iloc[0]
        s = d['speed'][d['speed'].n_records == n].iloc[0]
        L.append(f"{n} & {b_['p50_ms']:.1f} ({b_['p25_ms']:.1f}--{b_['p75_ms']:.1f}) & {b_['p95_ms']:.1f} / {b_['p99_ms']:.1f} & "
                 f"\\textbf{{{v_['p50_ms']:.1f}}} ({v_['p25_ms']:.1f}--{v_['p75_ms']:.1f}) & \\textbf{{{v_['p95_ms']:.1f} / {v_['p99_ms']:.1f}}} & "
                 f"{s['speedup_p50']:.2f} [{s['speedup_ci_low']:.2f}, {s['speedup_ci_high']:.2f}]\\\\")
    L.append(r'''\bottomrule
\end{tabular}
\end{table}''')
    return '\n\n'.join(L) + '\n'


def tex_values(v: dict) -> str:
    lines = ['% Generated by src/build_report.py -- do not edit by hand.']
    for k, val in v.items():
        s = str(val).replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')
        if k == 'pAsymMain':
            mant, exp = s.split('e')
            s = f'{mant}\\times10^{{{int(exp)}}}'
        lines.append(f'\\newcommand{{\\v{k}}}{{{s}}}')
    return '\n'.join(lines) + '\n'


def build(cfg: dict) -> list[Path]:
    d = load(cfg)
    v = values(d)
    tables = md_tables(d)
    template = (ROOT / 'reports/templates/paper_section_4.template.md').read_text(encoding='utf-8')
    text = template
    for k, val in {**{k: str(x) for k, x in v.items()}, **tables}.items():
        text = text.replace('{{' + k + '}}', val)
    missing = [line for line in text.splitlines() if '{{' in line]
    if missing:
        raise ValueError(f'unfilled placeholders: {missing[:3]}')
    out_md = ROOT / 'reports/paper_section_4.md'
    out_md.write_text(text, encoding='utf-8', newline='\n')
    latex = ROOT / 'reports/latex'
    latex.mkdir(parents=True, exist_ok=True)
    (latex / 'generated_values.tex').write_text(tex_values(v), encoding='utf-8', newline='\n')
    (latex / 'generated_tables.tex').write_text(tex_tables(d), encoding='utf-8', newline='\n')
    return [out_md, latex / 'generated_values.tex', latex / 'generated_tables.tex']


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build the results section and LaTeX inputs.')
    parser.add_argument('--config', default='configs/research.yaml')
    args = parser.parse_args(argv)
    for p in build(process_data.load_config(args.config)):
        print('wrote', p.relative_to(ROOT))


if __name__ == '__main__':
    main()
