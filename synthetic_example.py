"""Synthetic algebra example. No provider connection, credentials or quantum hardware."""
import json
import numpy as np
from reference_readout import PinnedReadout


def main():
    header = [2, 9]
    a0 = np.array([[.97, .08], [.03, .92]])
    a1 = np.array([[.91, .02], [.09, .98]])
    prepared = np.array([.1, .2, .3, .4])
    measured = np.kron(a1, a0) @ prepared
    shots = 100000
    counts = np.rint(measured * shots).astype(int)
    calibration = {'readout': {'readoutArray': {
        '|0> readout fidelity': {'qubit_used': ['Q2', 'Q9'], 'param_list': [.97, .91]},
        '|1> readout fidelity': {'qubit_used': ['Q2', 'Q9'], 'param_list': [.92, .98]},
    }}}
    corrected = PinnedReadout(calibration).estimate(header, counts)
    other = np.kron(np.linalg.inv(a0), np.linalg.inv(a1)) @ (counts / counts.sum())
    other = np.clip(other, 0, 1)
    other /= other.sum()
    print(json.dumps({'kind': 'SYNTHETIC_ALGEBRA_NOT_QPU_OR_NATIVE_SDK',
        'physical_header': header, 'synthetic_shots': int(counts.sum()),
        'prepared_distribution': prepared.tolist(),
        'header_reference': corrected['probabilities_before_rounding'].tolist(),
        'opposite_factor_order': other.tolist(),
        'max_distribution_difference': float(np.max(np.abs(other - corrected['probabilities_before_rounding'])))}, indent=2))


if __name__ == '__main__':
    main()
