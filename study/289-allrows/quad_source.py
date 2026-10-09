"""Quadrature check: which radial average the x2/x3 pressure SOURCE needs.

Exact (S3/S4 of symbolic_rows.py): on both curved grids the x2/x3 pressure
source integrates p(r) against r dr, i.e. it needs the FACE average
<p>_A = int p r dr / int r dr -- the same average the x2/x3 pressure FLUX needs.
snapy's source multiplies the stored cell value pbar_V (weight r^2 dr).

Per cell of a hydrostatic column, 40-point Gauss-Legendre, compare against <p>_A:
   code       pbar_V                       (current source AND current flux)
   corrected  pbar_V - delta * D1(pbar_V)  (D1 centred on x1v, as e7f9904)
Expect code error ~ delta p' = O(h^2) (ratio 4 per halving) and corrected
error O(h^4) (ratio 16).  CPU: milliseconds.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

xg, wg = leggauss(40)


def cell_avg(f, rm, rp, k):
    r = 0.5 * (rp - rm)[:, None] * xg[None, :] + 0.5 * (rp + rm)[:, None]
    w = wg[None, :] * r**k
    return (f(r) * w).sum(1) / w.sum(1)


def run(R0, Hs, ncells, tag):
    p = lambda r: np.exp(-(R0 / Hs) * (1.0 - R0 / r))
    print(f'{tag}: R0={R0}, scale height {Hs}, column depth 0.5')
    print('    h        |code-<p>_A|/p   ratio   |corr-<p>_A|/p   ratio')
    prev = None
    for n in ncells:
        h = 0.5 / n
        x1f = R0 + h * np.arange(-1, n + 2)
        rm, rp = x1f[:-1], x1f[1:]
        x1v = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
        rb = 0.5 * (rm + rp); h2 = h * h
        dl = h2 * (12 * rb**2 - h2) / (12 * rb * (12 * rb**2 + h2))
        pV, pA = cell_avg(p, rm, rp, 2), cell_avg(p, rm, rp, 1)
        D1 = (pV[2:] - pV[:-2]) / (x1v[2:] - x1v[:-2])
        e_code = np.abs(pV[1:-1] - pA[1:-1]) / pA[1:-1]
        e_corr = np.abs(pV[1:-1] - dl[1:-1] * D1 - pA[1:-1]) / pA[1:-1]
        cur = (e_code.max(), e_corr.max())
        rat = ('', '') if prev is None else (f'{prev[0] / cur[0]:5.2f}', f'{prev[1] / cur[1]:5.2f}')
        print(f'  {h:.5f}   {cur[0]:.3e}      {rat[0]:>5}   {cur[1]:.3e}      {rat[1]:>5}')
        prev = cur


if __name__ == '__main__':
    run(1.0, 0.1, (8, 16, 32, 64, 128), 'deep shell   ')
    run(10.0, 0.1, (8, 16, 32, 64, 128), 'thin shell   ')
