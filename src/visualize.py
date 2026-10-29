"""Publication figures for Task 3 (Week 8).

Every figure follows the three course rules: labelled axes with units, visible uncertainty
(95% bootstrap CI and/or p25-p75 bands), and a colour-blind-safe palette (seaborn "colorblind")
combined with distinct markers and line styles so that series remain distinguishable in
grayscale print. Each figure is written as vector PDF and as 300 DPI PNG.

Usage::

    python src/visualize.py --config configs/research.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_data  # noqa: E402

ROOT = process_data.ROOT
PALETTE = sns.color_palette('colorblind')
COLOR = {'baseline_loop': PALETTE[0], 'vectorized': PALETTE[1],
         'main': PALETTE[0], 'five_level': PALETTE[2], 'adjusted': PALETTE[3], 'literature': PALETTE[7]}
MARKER = {'baseline_loop': 'o', 'vectorized': 's', 'main': 'o', 'five_level': 's', 'adjusted': 'D'}
IMPL_LABEL = {'baseline_loop': 'Baseline: Task 2 loop bootstrap', 'vectorized': 'Proposed: vectorised bootstrap'}
UPS_AXIS = 'UPS total score (points; range 6–24)'
FREQ_AXIS = 'Academic GenAI use frequency (ordinal level)'
# Matplotlib metadata keys are cleared so repeated runs write byte-identical PDFs.
PDF_META = {'CreationDate': None, 'ModDate': None, 'Producer': None, 'Creator': None}


def set_style() -> None:
    sns.set_theme(style='whitegrid', context='paper', font_scale=1.2, palette=PALETTE)
    plt.rcParams.update({'axes.edgecolor': '0.35', 'grid.color': '0.88', 'grid.linewidth': 0.6,
                         'lines.linewidth': 2.0, 'lines.markersize': 7, 'savefig.bbox': 'tight',
                         'legend.frameon': True, 'legend.framealpha': 0.95, 'pdf.fonttype': 42,
                         'svg.hashsalt': 'task3', 'figure.dpi': 100})


def save(fig, name: str, out_dir: Path, dpi: int = 300) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf, png = out_dir / f'{name}.pdf', out_dir / f'{name}.png'
    fig.savefig(pdf, metadata=PDF_META)
    fig.savefig(png, dpi=dpi, metadata={'Software': None})
    plt.close(fig)
    return [pdf, png]


def _freq_ticks(ax, levels):
    ax.set_xticks(list(levels))
    ax.set_xticklabels([f'{lv}\n{process_data.FREQUENCY_LABELS[lv]}' for lv in levels], fontsize=9.5)


# --------------------------------------------------------------------------------------
# Figure 1 - pipeline latency versus workload (engineering layer)
# --------------------------------------------------------------------------------------
def fig_latency_vs_load(latency: pd.DataFrame, out_dir: Path, dpi: int = 300):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    styles = {'p50': ('-', 'p50 (median)'), 'p95': ('--', 'p95'), 'p99': (':', 'p99')}
    for impl, g in latency.groupby('implementation'):
        g = g.sort_values('n_records')
        x = g['n_records'].to_numpy()
        c, m = COLOR[impl], MARKER[impl]
        ax.fill_between(x, g['p50_ci_low'], g['p50_ci_high'], color=c, alpha=0.22, linewidth=0)
        ax.fill_between(x, g['p95_ci_low'], g['p95_ci_high'], color=c, alpha=0.10, linewidth=0)
        for p, (ls, plabel) in styles.items():
            ax.plot(x, g[f'{p}_ms'], linestyle=ls, marker=m, color=c, markersize=6 if p == 'p50' else 5,
                    markerfacecolor=c if p == 'p50' else 'white', label=f'{IMPL_LABEL[impl]} – {plabel}')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(sorted(latency['n_records'].unique()))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('Workload size (survey records per run, log scale)')
    ax.set_ylabel('Pipeline latency per run (ms, log scale)')
    ax.set_title('Fig. 1. Analysis-pipeline latency versus workload\n'
                 '(benchmark phase only; shaded bands = 95% bootstrap CI of p50 and p95)', fontsize=11)
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=2, columnspacing=1.2)
    return save(fig, 'fig1_latency_vs_load', out_dir, dpi)


# --------------------------------------------------------------------------------------
# Figure 2 - distribution of UPS by AI-use frequency (survey layer)
# --------------------------------------------------------------------------------------
def fig_distribution_boxplot(main: pd.DataFrame, groups: pd.DataFrame, rho: dict, out_dir: Path,
                             seed: int, dpi: int = 300):
    g = groups[groups['sample'] == 'main_cleaned_n285'].sort_values('ai_frequency')
    levels = g['ai_frequency'].tolist()
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    data = [main.loc[main['ai_frequency'] == lv, 'ups_total'].to_numpy() for lv in levels]
    bp = ax.boxplot(data, positions=levels, widths=0.55, patch_artist=True, showfliers=False,
                    medianprops={'color': '0.15', 'linewidth': 1.6}, whiskerprops={'color': '0.35'},
                    capprops={'color': '0.35'}, boxprops={'edgecolor': '0.35', 'linewidth': 1.0})
    hatches = ['', '//', '..', 'xx']
    for patch, h in zip(bp['boxes'], hatches):
        patch.set_facecolor((*COLOR['main'], 0.18))
        patch.set_hatch(h)
    rng = np.random.default_rng(seed)
    for lv, v in zip(levels, data):
        jitter = rng.uniform(-0.18, 0.18, len(v))
        yj = v + rng.uniform(-0.18, 0.18, len(v))
        ax.scatter(lv + jitter, yj, s=9, color=COLOR['main'], alpha=0.35, linewidths=0, zorder=2)
    ax.errorbar(np.array(levels) + 0.36, g['median'], yerr=[g['median'] - g['median_ci_low'], g['median_ci_high'] - g['median']],
                fmt='D', color='0.1', markersize=6, capsize=4, elinewidth=1.4, label='Median with 95% bootstrap CI', zorder=4)
    for lv, n in zip(levels, g['n']):
        ax.text(lv, 25.0, f'n = {n}', ha='center', va='bottom', fontsize=9, color='0.25')
    _freq_ticks(ax, levels)
    ax.set_ylim(5, 26.5)
    ax.set_yticks(range(6, 25, 3))
    ax.set_xlabel(FREQ_AXIS)
    ax.set_ylabel(UPS_AXIS)
    lo, hi = rho['ci95_percentile_bootstrap']
    ax.set_title('Fig. 2. Unintentional procrastination by academic GenAI use frequency\n'
                 f'(n = {rho["n"]}; Spearman ρ = {rho["spearman_rho"]:.2f}, 95% CI {lo:.2f}–{hi:.2f}; '
                 'box = p25–p75, whiskers = 1.5 IQR)', fontsize=10.5)
    ax.legend(loc='lower right', fontsize=9)
    return save(fig, 'fig2_distribution_boxplot', out_dir, dpi)


# --------------------------------------------------------------------------------------
# Figure 3 - dose-response style summary with uncertainty (survey layer)
# --------------------------------------------------------------------------------------
def fig_ups_vs_frequency(groups: pd.DataFrame, out_dir: Path, dpi: int = 300):
    main = groups[groups['sample'] == 'main_cleaned_n285'].sort_values('ai_frequency')
    five = groups[groups['sample'] == 'sensitivity_b_raw_five_level'].sort_values('ai_frequency')
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.fill_between(main['ai_frequency'], main['p25'], main['p75'], color=COLOR['main'], alpha=0.12,
                    linewidth=0, label='Main sample: p25–p75 band')
    ax.errorbar(main['ai_frequency'] - 0.06, main['median'],
                yerr=[main['median'] - main['median_ci_low'], main['median_ci_high'] - main['median']],
                fmt='-o', color=COLOR['main'], capsize=4, label='Main sample (n = 285): median ± 95% CI')
    ax.errorbar(main['ai_frequency'] + 0.0, main['mean'],
                yerr=[main['mean'] - main['mean_ci_low'], main['mean_ci_high'] - main['mean']],
                fmt='--^', color=COLOR['main'], markerfacecolor='white', capsize=4,
                label='Main sample (n = 285): mean ± 95% CI')
    ax.errorbar(five['ai_frequency'] + 0.06, five['mean'],
                yerr=[five['mean'] - five['mean_ci_low'], five['mean_ci_high'] - five['mean']],
                fmt=':s', color=COLOR['five_level'], capsize=4,
                label=f'Raw five-level sample (n = {int(five["n"].sum())}): mean ± 95% CI')
    ref = five[five['ai_frequency'] == 0]
    ax.annotate('Reference group\n(rarely/never, n = %d)' % int(ref['n'].iloc[0]),
                xy=(0.06, float(ref['mean'].iloc[0])), xytext=(0.35, 7.3), fontsize=8.5,
                arrowprops={'arrowstyle': '->', 'color': '0.35', 'lw': 0.8}, color='0.25')
    _freq_ticks(ax, range(0, 5))
    ax.set_ylim(6, 20)
    ax.set_xlabel(FREQ_AXIS)
    ax.set_ylabel(UPS_AXIS)
    ax.set_title('Fig. 3. UPS score across AI-use levels with 95% bootstrap confidence intervals', fontsize=11)
    ax.legend(fontsize=8, loc='upper left')
    return save(fig, 'fig3_ups_vs_ai_frequency', out_dir, dpi)


# --------------------------------------------------------------------------------------
# Figure 4 - effect-size forest plot across analyses
# --------------------------------------------------------------------------------------
def fig_effect_forest(assoc: list[dict], models: dict, out_dir: Path, dpi: int = 300):
    rows = [
        ('Main: supplied cleaned file (n = %d)' % assoc[0]['n'], assoc[0]['spearman_rho'], *assoc[0]['ci95_percentile_bootstrap'], 'main', 'Spearman ρ'),
        ('Sensitivity A: raw file, independent rules (n = %d)' % assoc[1]['n'], assoc[1]['spearman_rho'], *assoc[1]['ci95_percentile_bootstrap'], 'main', 'Spearman ρ'),
        ('Sensitivity B: raw file incl. rarely/never (n = %d)' % assoc[2]['n'], assoc[2]['spearman_rho'], *assoc[2]['ci95_percentile_bootstrap'], 'five_level', 'Spearman ρ'),
        ('Adjusted OLS: age, gender, education (n = %d)' % models['n'], models['proposed']['standardised_beta'],
         *models['proposed']['standardised_beta_ci95_hc3'], 'adjusted', 'standardised β'),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for i, (label, est, lo, hi, key, metric) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt=MARKER[key], color=COLOR[key], capsize=4,
                    markersize=8, elinewidth=1.8)
        ax.text(hi + 0.015, y, f'{metric} = {est:.2f} [{lo:.2f}, {hi:.2f}]', va='center', fontsize=8.5, color='0.2')
    ax.axvline(0, color='0.3', linewidth=1.0)
    ax.text(0.005, len(rows) - 0.45, 'H₀ baseline: no association', fontsize=8, color='0.3')
    ax.axvline(0.309, color=COLOR['literature'], linewidth=1.2, linestyle='--')
    ax.text(0.314, -0.75, 'Abbas et al. (2024): β = 0.31\n(general procrastination, different scale)',
            fontsize=7.5, color='0.35', va='bottom')
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=9)
    ax.set_xlim(-0.05, 0.75)
    ax.set_ylim(-0.9, len(rows) - 0.3)
    ax.set_xlabel('Effect size (dimensionless; point estimate with 95% CI)')
    ax.set_title('Fig. 4. Association estimates across main, sensitivity and adjusted analyses', fontsize=11)
    return save(fig, 'fig4_effect_size_forest', out_dir, dpi)


# --------------------------------------------------------------------------------------
# Figure 5 - latency distributions and the warm-up runs that were excluded
# --------------------------------------------------------------------------------------
def fig_latency_distribution(log: pd.DataFrame, out_dir: Path, dpi: int = 300):
    ok = log[log['status'] == 'ok'].copy()
    workloads = sorted(ok['n_records'].unique())
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    offsets = {'baseline_loop': -0.2, 'vectorized': 0.2}
    for impl, off in offsets.items():
        bench = [ok[(ok['implementation'] == impl) & (ok['phase'] == 'benchmark') & (ok['n_records'] == n)]['latency_ms']
                 for n in workloads]
        pos = np.arange(len(workloads)) + off
        bp = ax.boxplot(bench, positions=pos, widths=0.34, patch_artist=True, showfliers=True,
                        flierprops={'marker': MARKER[impl], 'markersize': 3.5, 'markerfacecolor': 'none',
                                    'markeredgecolor': COLOR[impl]},
                        medianprops={'color': '0.1', 'linewidth': 1.5},
                        boxprops={'edgecolor': COLOR[impl], 'linewidth': 1.2},
                        whiskerprops={'color': COLOR[impl]}, capprops={'color': COLOR[impl]})
        for patch in bp['boxes']:
            patch.set_facecolor((*COLOR[impl], 0.25))
            patch.set_hatch('' if impl == 'baseline_loop' else '//')
        warm = ok[(ok['implementation'] == impl) & (ok['phase'] == 'warmup')]
        wx = np.array([workloads.index(n) for n in warm['n_records']]) + off
        ax.scatter(wx, warm['latency_ms'], marker='x', color='0.15', s=22, linewidths=1.0, zorder=4,
                   label='Warm-up runs (excluded)' if impl == 'baseline_loop' else None)
        ax.plot([], [], marker=MARKER[impl], color=COLOR[impl], linestyle='-', label=IMPL_LABEL[impl] + ' (benchmark runs)')
    ax.set_yscale('log')
    ax.set_xticks(range(len(workloads)))
    ax.set_xticklabels([str(n) for n in workloads])
    ax.set_xlabel('Workload size (survey records per run)')
    ax.set_ylabel('Pipeline latency per run (ms, log scale)')
    ax.set_title('Fig. 5. Latency distributions per condition (box = p25–p75, whiskers = 1.5 IQR)\n'
                 'with the discarded warm-up runs overlaid', fontsize=11)
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, columnspacing=1.2)
    return save(fig, 'fig5_latency_distribution', out_dir, dpi)


def make_all(cfg: dict) -> list[Path]:
    set_style()
    out = ROOT / cfg['reports']['figures_dir']
    dpi = cfg['reports']['dpi']
    proc = ROOT / cfg['processed']['dir']
    import json
    results = json.loads((ROOT / cfg['reports']['results_json']).read_text(encoding='utf-8'))
    assoc = results['survey']['association']
    main = pd.read_csv(ROOT / cfg['processed']['main'])
    groups = pd.read_csv(proc / 'survey_group_summary.csv')
    latency = pd.read_csv(proc / 'pipeline_latency_summary.csv')
    log = process_data.load_jsonl(ROOT / cfg['benchmark']['log_path'])
    paths = []
    paths += fig_latency_vs_load(latency, out, dpi)
    paths += fig_distribution_boxplot(main, groups, assoc[0], out, cfg['seed'], dpi)
    paths += fig_ups_vs_frequency(groups, out, dpi)
    paths += fig_effect_forest(assoc, results['survey']['models_main'], out, dpi)
    paths += fig_latency_distribution(log, out, dpi)
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description='Render Task 3 figures (PDF + 300 DPI PNG).')
    parser.add_argument('--config', default='configs/research.yaml')
    args = parser.parse_args(argv)
    cfg = process_data.load_config(args.config)
    for p in make_all(cfg):
        print('wrote', p.relative_to(ROOT))


if __name__ == '__main__':
    main()
