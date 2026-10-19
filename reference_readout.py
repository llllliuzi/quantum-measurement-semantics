"""Ordinary pinned-calibration reference; independently assemble forward channel.

Small-register control, not M3 reproduction or a new mitigation algorithm.
Rows = measured integer outcomes, columns = prepared integer outcomes;
physical header column k is integer bit k. No inverse-Kronecker implementation.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np
from scipy.linalg import lu_factor, lu_solve

class PinnedReadout:
    def __init__(self, calibration):
        self.calibration=json.loads(json.dumps(calibration))
        self.sha256=hashlib.sha256(json.dumps(self.calibration,sort_keys=True).encode()).hexdigest()
        self.factors={}

    def estimate(self, header, counts):
        header=tuple(header)
        if header not in self.factors:
            arr=self.calibration['readout']['readoutArray']
            f0=dict(zip(arr['|0> readout fidelity']['qubit_used'],arr['|0> readout fidelity']['param_list']))
            f1=dict(zip(arr['|1> readout fidelity']['qubit_used'],arr['|1> readout fidelity']['param_list']))
            n=len(header);indices=np.arange(1<<n);channel=np.ones((1<<n,1<<n))
            for k,q in enumerate(header):
                measured=((indices>>k)&1)[:,None];prepared=((indices>>k)&1)[None,:]
                a=f0[f'Q{q}'];b=f1[f'Q{q}']
                conditional=np.where(prepared==0,np.where(measured==0,a,1-a),np.where(measured==0,1-b,b))
                channel*=conditional
            if not np.allclose(channel.sum(axis=0),1,atol=1e-12):raise ValueError('Invalid assignment channel')
            self.factors[header]=lu_factor(channel)
        p=lu_solve(self.factors[header],np.asarray(counts,dtype=float)/sum(counts))
        p=np.clip(p,0,1);p=p/p.sum()
        pseudo=np.floor(p*sum(counts)+.5)
        return {'probabilities_before_rounding':p,'counts':pseudo,
                'probabilities':pseudo/pseudo.sum(),'header':header,'calibration_sha256':self.sha256}
