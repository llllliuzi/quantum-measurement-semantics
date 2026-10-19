"""Create SVG figures from public derived data; all outcomes are historical."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent


def main():
    rows = json.loads((ROOT / 'data/energy_scale.json').read_text(encoding='utf-8'))
    example = json.loads((ROOT / 'data/estimator_paths.json').read_text(encoding='utf-8'))['example']
    ids = list(dict.fromkeys(r['evaluation'] for r in rows))
    plt.rcParams.update({'font.size': 8, 'svg.fonttype': 'none', 'axes.spines.top': False, 'axes.spines.right': False})
    out = ROOT / 'outputs'
    out.mkdir(exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.6), layout='constrained')
    for k, (color, marker) in enumerate([('#255b78', 'o'), ('#238a80', 's'), ('#99671b', '^')]):
        lookup = {r['evaluation']: r for r in rows if r['calibration_index'] == k}
        axs[0].scatter(range(1, 57), [lookup[key]['ratio_to_raw_CI_halfwidth'] for key in ids],
            color=color, marker=marker, s=12, alpha=.8, label='ABC'[k])
    axs[0].set(xlabel='Energy record (56 per saved calibration)', ylabel='Order difference / raw interval half-width',
               ylim=(0, .32), title='(a) Matched descriptive scale')
    axs[0].legend(loc='upper right', ncol=3, frameon=False, fontsize=7)
    axs[1].plot([0], [example['raw']], 'D', color='.4', label='Raw')
    axs[1].plot([1, 2, 3], example['auto'], 'o-', color='#255b78', label='SDK auto')
    axs[1].plot([1, 2, 3], example['header_reference'], 's-', color='#238a80', label='Header reference')
    axs[1].set(xticks=[0, 1, 2, 3], xticklabels=['Raw', 'A', 'B', 'C'], xlabel='Read policy / saved calibration',
               ylabel='Energy/spin', ylim=(-1.084, -1.063), title='(b) Estimator paths (zoom)')
    axs[1].legend(loc='lower left', frameon=False, fontsize=7)
    for ax in axs:
        ax.grid(axis='y', alpha=.17)
    fig.savefig(out / 'measurement_semantics.svg')
    plt.close(fig)
    points = json.loads((ROOT / 'data/application_curve.json').read_text(encoding='utf-8'))
    fig, ax = plt.subplots(figsize=(3.5, 2.35), layout='constrained')
    for config in ['block4_layer1', 'block8_layer1', 'block4_layer3', 'block8_layer3']:
        p = [r for r in points if r['configuration'] == config]
        color = '#255b78' if 'block4' in config else '#238a80'
        deep = 'layer3' in config
        marker = ('^' if 'block4' in config else 'D') if deep else ('o' if 'block4' in config else 's')
        for final in [False, True]:
            q = [r for r in p if r['independent_final'] == final]
            ax.errorbar([r['x'] for r in q], [r['energy'] for r in q],
                yerr=[[r['lower_error'] for r in q], [r['upper_error'] for r in q]],
                color=color, marker=marker, ms=2.6, lw=.75, elinewidth=.55, capsize=1.5,
                ls='none' if final else ('--' if deep else '-'), label=None if final else config.replace('_', ', '))
    ax.axhline(-1.2297439309324267, ls=':', color='.5', lw=.65)
    ax.set(xlabel='Update / independent final (F)', ylabel='Energy/spin', xlim=(-.25, 6.35), ylim=(-1.28, -.35),
        xticks=[0, 1, 2, 3, 4, 6], xticklabels=['0', '1', '2', '3', '4', 'F'])
    ax.legend(loc='upper right', ncol=2, frameon=False, fontsize=5.5, columnspacing=.5)
    ax.grid(axis='y', alpha=.15)
    fig.savefig(out / 'application_context.svg')
    plt.close(fig)
    print('Saved outputs/measurement_semantics.svg and outputs/application_context.svg')


if __name__ == '__main__':
    main()
