"""Build the generated inputs of the IEEE paper from the committed analysis outputs.

Run from the repository root after ``python src/run_pipeline.py``:

    python paper/make_assets.py

It copies the LaTeX value macros written by ``src/build_report.py`` and draws the two
column-width result figures, so every number and plot in the paper comes from
``reports/results.json`` and ``data/processed/``.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper' / 'generated'
COLUMN_IN = 3.45  # IEEE two-column text width is about 3.5 in
PALETTE = sns.color_palette('colorblind')


def style() -> None:
    plt.rcParams.update({
        'font.family': 'serif', 'font.serif': ['STIXGeneral'], 'mathtext.fontset': 'stix',
        'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 8, 'legend.fontsize': 7,
        'xtick.labelsize': 7, 'ytick.labelsize': 7, 'axes.linewidth': 0.6,
        'pdf.fonttype': 42, 'svg.hashsalt': 'kussain-zhakyp', 'figure.dpi': 100,
    })


def save(fig, name: str) -> None:
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight', pad_inches=0.02, metadata={'CreationDate': None})
    plt.close(fig)


def fig_effects(res: dict) -> None:
    assoc = {a['analysis']: a for a in res['survey']['association']}
    beta = res['survey']['models_main']['proposed']
    rows = [
        ('Main sample ($n$=285), $\\hat\\rho_s$', assoc['main_cleaned_n285']['spearman_rho'],
         assoc['main_cleaned_n285']['ci95_percentile_bootstrap'], 'o', PALETTE[0]),
        ('Sensitivity A ($n$=303), $\\hat\\rho_s$', assoc['sensitivity_a_raw_independent']['spearman_rho'],
         assoc['sensitivity_a_raw_independent']['ci95_percentile_bootstrap'], 's', PALETTE[1]),
        ('Sensitivity B ($n$=327), $\\hat\\rho_s$', assoc['sensitivity_b_raw_five_level']['spearman_rho'],
         assoc['sensitivity_b_raw_five_level']['ci95_percentile_bootstrap'], '^', PALETTE[2]),
        ('Adjusted model, standardised $\\beta$', beta['standardised_beta'],
         beta['standardised_beta_ci95_hc3'], 'D', PALETTE[3]),
    ]
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 1.7))
    for i, (label, est, (lo, hi), marker, colour) in enumerate(rows):
        ax.errorbar(est, i, xerr=[[est - lo], [hi - est]], fmt=marker, color=colour, ms=4.5,
                    capsize=2.5, lw=1.1, mfc='white' if marker in ('s', 'D') else colour)
        ax.text(hi + 0.012, i, f'{est:.2f} [{lo:.2f}, {hi:.2f}]', va='center', fontsize=6.5)
    ax.axvline(0, color='0.3', lw=0.8)
    ax.axvline(0.309, color='0.45', lw=0.8, ls='--')
    ax.text(0.006, -0.62, '$H_0$: no association', fontsize=6.5, color='0.3', va='center')
    ax.text(0.317, -0.62, 'Abbas et al. (2024): $\\beta$ = 0.31', fontsize=6.5, color='0.35', va='center')
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_ylim(3.45, -0.85)
    ax.set_xlim(-0.03, 0.62)
    ax.set_xlabel('Effect estimate with 95% interval (unitless)')
    ax.grid(axis='x', lw=0.3, color='0.85')
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    save(fig, 'fig_effects')


def fig_latency() -> None:
    lat = pd.read_csv(ROOT / 'data/processed/pipeline_latency_summary.csv')
    labels = {'baseline_loop': ('Baseline: loop bootstrap', 'o', PALETTE[0], '-'),
              'vectorized': ('Proposed: vectorised bootstrap', 's', PALETTE[1], '--')}
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 1.85))
    for impl, (label, marker, colour, ls) in labels.items():
        d = lat[lat['implementation'] == impl].sort_values('n_records')
        ax.fill_between(d['n_records'], d['p50_ci_low'], d['p50_ci_high'], color=colour, alpha=0.18, lw=0)
        ax.plot(d['n_records'], d['p50_ms'], marker=marker, ls=ls, color=colour, ms=4, lw=1.1, label=label,
                mfc='white' if marker == 's' else colour)
    sp = pd.read_csv(ROOT / 'data/processed/pipeline_speedup.csv').set_index('n_records')
    for n in (50, 285, 2000):
        y = lat[(lat['implementation'] == 'vectorized') & (lat['n_records'] == n)]['p50_ms'].iloc[0]
        ax.annotate(f'{sp.loc[n, "speedup_p50"]:.1f}$\\times$', (n, y), textcoords='offset points',
                    xytext=(0, 5), ha='center', va='bottom', fontsize=6.5)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks([50, 100, 285, 500, 1000, 2000], ['50', '100', '285', '500', '1000', '2000'])
    ax.minorticks_off()
    ax.set_ylim(8, 1500)
    ax.set_xlabel('Workload size (records per run, log scale)')
    ax.set_ylabel('Median latency p50 (ms, log)')
    ax.grid(lw=0.3, color='0.85')
    ax.set_axisbelow(True)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, handlelength=2.0,
              columnspacing=1.0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    save(fig, 'fig_latency')


def _p(value: float) -> str:
    return '<0.001' if value < 0.001 else f'{value:.3f}'


def paper_values() -> None:
    """Extra macros (letters-only names) for the group comparisons and benchmark rows."""
    words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 50: 'Fifty', 285: 'TwoEightyFive', 2000: 'TwoThousand'}
    lines = ['% Generated by paper/make_assets.py -- do not edit by hand.']
    groups = pd.read_csv(ROOT / 'data/processed/survey_group_summary.csv')
    for _, g in groups[groups['sample'] == 'main_cleaned_n285'].iterrows():
        lines.append(f"\\newcommand{{\\pMed{words[int(g['ai_frequency'])]}}}{{{g['median']:.1f}}}")
    refs = pd.read_csv(ROOT / 'data/processed/survey_reference_comparisons.csv')
    for sample, tag in (('main_cleaned_n285', ''), ('sensitivity_b_raw_five_level', 'B')):
        for _, r in refs[refs['sample'] == sample].iterrows():
            w = words.get(int(r['ai_frequency']))
            if w is None:
                continue
            lines += [f"\\newcommand{{\\pDelta{tag}{w}}}{{{r['cliffs_delta']:.2f}}}",
                      f"\\newcommand{{\\pDelta{tag}{w}Ci}}{{[{r['cliffs_delta_ci_low']:.2f}, {r['cliffs_delta_ci_high']:.2f}]}}",
                      f"\\newcommand{{\\pHolm{tag}{w}}}{{{_p(r['p_value_holm'])}}}",
                      f"\\newcommand{{\\pMedDiff{tag}{w}}}{{{r['median_difference']:+.1f}}}"]
    lat = pd.read_csv(ROOT / 'data/processed/pipeline_latency_summary.csv')
    sp = pd.read_csv(ROOT / 'data/processed/pipeline_speedup.csv').set_index('n_records')
    for n in (50, 285, 2000):
        w = words[n]
        for impl, tag in (('baseline_loop', 'Loop'), ('vectorized', 'Vec')):
            row = lat[(lat['implementation'] == impl) & (lat['n_records'] == n)].iloc[0]
            lines += [f"\\newcommand{{\\pLat{tag}{w}}}{{{row['p50_ms']:.1f}}}",
                      f"\\newcommand{{\\pLatHigh{tag}{w}}}{{{row['p95_ms']:.1f}}}"]
        lines += [f"\\newcommand{{\\pSpeed{w}}}{{{sp.loc[n, 'speedup_p50']:.2f}}}",
                  f"\\newcommand{{\\pSpeed{w}Ci}}{{[{sp.loc[n, 'speedup_ci_low']:.2f}, {sp.loc[n, 'speedup_ci_high']:.2f}]}}"]
    (OUT / 'paper_values.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'reports/latex/generated_values.tex', OUT / 'values.tex')
    res = json.loads((ROOT / 'reports/results.json').read_text(encoding='utf-8'))
    paper_values()
    style()
    fig_effects(res)
    fig_latency()
    print('wrote', ', '.join(sorted(p.name for p in OUT.iterdir() if p.suffix in ('.tex', '.pdf'))))


if __name__ == '__main__':
    main()
