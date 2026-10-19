"""Recompute reported descriptive quantities from published derived data (stdlib only)."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


def main():
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('File hash mismatch: ' + name)
    rows = load('energy_scale.json')
    native = load('native_reference_checks.json')
    changes = load('update_comparisons.json')
    account = load('acquisition_accounting.json')
    differences = [r['native'] - r['standard'] for r in rows]
    worst = max(rows, key=lambda r: r['absolute_order_discrepancy'])
    groups = []
    for k in range(3):
        g = [r for r in rows if r['calibration_index'] == k]
        groups.append({'calibration': 'ABC'[k], 'conditions': len(g),
                       'max_scale_ratio': max(r['ratio_to_raw_CI_halfwidth'] for r in g),
                       'positive': sum(r['native'] > r['standard'] for r in g),
                       'negative': sum(r['native'] < r['standard'] for r in g)})
    scalar_error = 0.
    for r in changes:
        k = r['step']
        for method in ['native', 'standard']:
            contrast = r[method + '_contrast']
            for theta, delta, saved in zip(r['original_parent'], r['delta'], r[method + '_update']):
                move = max(-.18, min(.18, .05 * k**(-.602) * contrast / (2 * .12 * k**(-.101)) * delta))
                reconstructed = (theta - move + math.pi) % (2 * math.pi) - math.pi
                scalar_error = max(scalar_error, abs(reconstructed - saved))
    totals = account['total']
    if totals['requested'] != totals['returned'] + totals['failed_requested'] or totals['unclassified'] != 0:
        raise ValueError('Acquisition partition does not close')
    ratio = worst['absolute_order_discrepancy'] / worst['raw_descriptive_CI_halfwidth']
    result = {
        'scope': 'Derived-data arithmetic; raw QPU/native replay is not independently rerun',
        'energy_calibration_conditions': len(rows), 'unique_energy_records': len({r['evaluation'] for r in rows}),
        'native_job_calibration_conditions': len(native),
        'nonzero_native_header_distribution_differences': sum(r['native_vs_standard_TV'] > 1e-12 for r in native),
        'signed_energy_positive': sum(d > 1e-12 for d in differences),
        'signed_energy_negative': sum(d < -1e-12 for d in differences),
        'signed_energy_range': [min(differences), max(differences)],
        'max_absolute_energy_difference': worst['absolute_order_discrepancy'],
        'matched_raw_interval_halfwidth': worst['raw_descriptive_CI_halfwidth'],
        'max_normalized_difference': max(r['ratio_to_raw_CI_halfwidth'] for r in rows),
        'calibration_groups': groups,
        'update_conditions': len(changes), 'gradient_sign_changes': sum(r['sign_change'] for r in changes),
        'max_coordinate_update_difference_rad': max(r['max_coordinate_update_difference'] for r in changes),
        'scalar_update_reconstruction_error': scalar_error,
        'acquisition_totals': totals,
        'conditional_precision_projection': {'assumed_fixed_difference': worst['absolute_order_discrepancy'],
            'formal_crossover_multiplier': ratio**-2, 'ratio_at_16': 4 * ratio,
            'status': 'Conditional extrapolation; not a high-shot experiment, significance forecast or physical bias bound'},
        'new_QPU_jobs': 0,
    }
    out = ROOT / 'outputs'
    out.mkdir(exist_ok=True)
    (out / 'recomputed_summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
