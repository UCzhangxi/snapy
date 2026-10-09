# Why the default x1 WB reference is first order at the wall faces, and a minimal fix

Code: `UCzhangxi/snapy` `next/curved-gravity-work-wb` @ 37dce4e, `SNAP_WB_REF4` off, `wb-wall-clamp: true`
(the default, `hydro_options.cpp:57`). Replica: `study/wb-ref4-onset/wallfix.py` (rest face density) and
`wallfix_growth.py` (onset growth rate); tables in `study/wb-ref4-onset/runs/wallfix_*`.

## 1. The rest face density
At linear order the reference enters only through the rest face density of the x1 mass flux
(`hydro_forward.cpp:269-274` subtract, `:276-292` even-parity ghosts, `:310-315` restore):
$$\rho_{f0}=\mathcal R_{\rm even}\big[\bar\rho-d_{\rm ref}\big]_f+d_{{\rm sf},f},$$
where $\mathcal R_{\rm even}$ is WENO5 applied with the even-parity wall ghosts $\rho'_{i_s-m}=\rho'_{i_s+m-1}$.
The kernel (`hydro_ref_x1_impl.h`):
* `:68-78` `rop_smooth`: $r^s_i=\tfrac1{16}(r_{i-2}+4r_{i-1}+6r_i+4r_{i+1}+r_{i+2})$, $r=\bar\rho/\bar p$, with every read index **clamped** to $[j_{lo},j_{hi}]$;
* `:159-160` $j_{lo}=i_l$, $j_{hi}=i_u$ at a clamped physical wall, i.e. **edge replication**;
* `:166-167` $d_{{\rm ref},i}=p_{{\rm ref},i}\,r^s_i$ and $d_{{\rm sf},i}=p_{{\rm sf},i-1/2}\,\tfrac12(r^s_{i-1}+r^s_i)$.

The pair is consistent when $r^s-r$ is a **smooth** field. $\mathcal R$ reproduces the smooth $d_{\rm ref}$ error that $d_{\rm sf}$ carries, and what is left is the interior $\tfrac{\Delta z^2}{12}(p'R'+2pR'')$ (`docs/derivations/wb-ref4.md` §2).

## 2. Edge replication is not exact for a linear profile
Let $r=a+bj$ near the bottom wall, with $j=i-i_l$ and $b=r_z\Delta z$.
* Wall cell $j=0$ reads $(r_0,r_0,r_0,r_1,r_2)$: $r^s_0=a+\tfrac{4\cdot1+1\cdot2}{16}b=r_0+\tfrac38 b$.
* Next cell $j=1$ reads $(r_0,r_0,r_1,r_2,r_3)$: $r^s_1=a+\tfrac{6+8+3}{16}b=r_1+\tfrac1{16}b$.
* Cells $j\ge2$ read no clamped value: $r^s_j=r_j+\tfrac{\Delta z^2}{2}r''+O(\Delta z^4)$ ($B$ has unit sum and second moment 1).

So $r^s$ has an $O(\Delta z)$ step, $D_0=\tfrac38$ and $D_1=\tfrac1{16}$ in units of $r_z\Delta z$, confined to the two wall cells. In units of $p\,r_z\Delta z$:
$$\rho'_0=-D_0,\quad\rho'_1=-D_1\quad(\text{ghosts: }\rho'_{-1}=-D_0,\ \rho'_{-2}=-D_1,\ \rho'_{-3}=0),\qquad
\delta d_{{\rm sf},1}=\tfrac12(D_0+D_1),\quad\delta d_{{\rm sf},2}=\tfrac12 D_1 .$$

## 3. The face error, exactly
WENO5 at linear weights: the right state at face $f$ is $(-3,27,47,-13,2)/60$ on cells $f-2..f+2$; the left state is $(2,-13,47,27,-3)/60$ on cells $f-3..f+1$. Then $\delta\rho_f/(p\,r_z\Delta z)=K_f$ with

| face (from the bottom wall) | $\mathcal R_{\rm even}[\rho']$ | $\delta d_{\rm sf}$ | $K_f$ | replica, NH 3, $n_z$ 64 |
|---|---|---|---|---|
| 1, right | $(-24D_0-47D_1)/60=-0.19896$ | $0.21875$ | $+0.0198$ | $+0.018$ |
| 1, left | $(-34D_0-29D_1)/60=-0.24271$ | $0.21875$ | $-0.0240$ | |
| 2, right | $(3D_0-27D_1)/60=-0.00938$ | $0.03125$ | $+0.0219$ | $+0.022$ |
| 2, left | $(11D_0-47D_1)/60=+0.01979$ | $0.03125$ | $+0.0510$ | $+0.053$ |
| 3, left | $(-2D_0+13D_1)/60=+0.00104$ | $0$ | $+0.0010$ | $+0.0011$ |

(Replica column: the measured relative error divided by $p\,r_z\Delta z/\rho=\beta\Delta z/T$, after subtracting the smooth interior part.) For an ideal gas $p\,r_z/\rho=\beta/T$, so
$$\frac{\delta\rho_f}{\rho}=K_f\,\frac{\beta}{T}\,\Delta z:\quad\textbf{first order},$$
on faces 1 and 2 at each wall (face 3 is first order too, but 20–50× smaller). The top wall is the mirror image, with the sign set by $r_z$ there. The wall face itself has $\bar u=0$ at a reflecting wall, so its density never enters a flux.

**Why the pair does not cancel it.** The cancellation needs $d_{\rm sf}=\mathcal R_{\rm even}[d_{\rm ref}]$ at the face. Here $d_{\rm sf}$ is a two-point mean of $r^s$ (weights $\tfrac12,\tfrac12$), while $\mathcal R_{\rm even}$ applies five WENO weights, with even ghosts, to the step $\rho'=-p\,(r^s-r)$. For a smooth $r^s-r$ the two agree to $O(\Delta z^2)$. For a two-cell step of height $O(\Delta z)$ they differ at $O(1)$ times the step. Both ingredients the lead named are needed: the clamped binomial makes the step, and the even-parity ghost fill (`hydro_forward.cpp:282-290`) makes $\mathcal R_{\rm even}$ of the step differ from the mean.

## 4. Minimal fix
**Cubic wall values in `rop_smooth`.** When a read index falls past a clamped wall, use the cubic extrapolation, in cell index, of the four owned cells next to the wall instead of the edge value:
$$r_{j_{lo}-m}\leftarrow\sum_{q=0}^{3}E_{m,q}\,r_{j_{lo}+q},\qquad
E_1=(4,-6,4,-1),\ E_2=(10,-20,15,-4),\ E_3=(20,-45,36,-10),$$
and the mirror image at $j_{hi}$ ($E_3$ is needed only by the ghost cell next to the wall, which feeds $d_{\rm sf}$ at the wall face). $B$ then sees a cubic-exact extension, so $r^s_i=r_i+\tfrac{\Delta z^2}{2}r''+O(\Delta z^4)$ **up to the wall**, the same smooth field as in the interior. The step disappears, and the pair cancels as in the interior.

Sketch (not applied to any PR branch), `hydro_ref_x1_impl.h:71-76`:
```cpp
for (int m = -2; m <= 2; ++m) {
  int j = i + m;
  T v;
  if (j < jlo && jlo > 0 /* clamped wall below */ && jhi - jlo >= 3) {
    v = extrap(w, ncells, flat, jlo, +1, jlo - j);   // sum_q E[jlo-j][q] r(jlo+q)
  } else if (j > jhi && jhi < nc1 - 1 && jhi - jlo >= 3) {
    v = extrap(w, ncells, flat, jhi, -1, j - jhi);   // sum_q E[j-jhi][q] r(jhi-q)
  } else {
    j = j < jlo ? jlo : (j > jhi ? jhi : j);
    v = w[IDN * ncells + flat + j] / w[IPR * ncells + flat + j];
  }
  if (!(v > T(0))) v = edge value;                    // positivity: keep today's read
  ...
}
```
* **Scope.** Only reads past a clamped wall change. $r^s$ changes at the two owned cells per wall (and at the ghost cells, which affect only $d_{\rm sf}$ at the wall face). $d_{\rm ref}$ changes at those two cells, and $d_{\rm sf}$ at faces $i_l..i_l+2$. Through the WENO stencils of $\rho'$ the face densities change at faces up to $i_l+4$. Faces $i_l+5..i_u-3$ and every cell from $i_l+2$ to $i_u-2$ are bitwise unchanged. At rest $\bar u=0$, so the rest balance is untouched (the reference density never enters the momentum pairing).
* **Guards.** With fewer than four owned cells, keep edge replication (W uses the same condition, `wb_ref4.cpp:114`). A non-positive extrapolated $r$ (an unresolved top) falls back to the edge value.
* **Why cubic and not linear.** Linear extrapolation, or a linear-exact two-cell closure such as $r^s_0=r_0$, $r^s_1=(r_0+2r_1+r_2)/4$ (column "lin" below), is also second order. But it leaves an $O(\Delta z^2)$ jump in $r^s-r$ against the interior bias $\tfrac{\Delta z^2}{2}r''$, so the wall faces get a different, non-smooth $O(\Delta z^2)$ error. With the cubic extension the wall faces carry the interior offset itself.

## 5. Order table (rest column, NH 3, $\epsilon=10^{-3}$; relative error $(\rho_f-\rho(z_f))/\rho(z_f)$)
Columns: faces 1, 2 (R, L) and 3 (L) above the bottom wall; faces 1, 2 (L, R) and 3 (R) below the top wall; the interior maximum (faces 5..$n_z$−5). The orders are $\log_2$ of successive ratios. Full tables: `runs/wallfix_faces_3H.txt`, `runs/wallfix_faces_1H.txt`.

| ref | $n_z$ | b1 R | b2 R | b2 L | t1 L | t2 R | interior |
|---|---|---|---|---|---|---|---|
| default | 16 | $+4.9\times10^{-4}$ | $+8.6\times10^{-4}$ | $+2.1\times10^{-3}$ | $-2.8\times10^{-3}$ | $-3.3\times10^{-3}$ | $1.7\times10^{-4}$ |
| | 32 | $+3.0\times10^{-4}$ | $+4.1\times10^{-4}$ | $+9.9\times10^{-4}$ | $-1.1\times10^{-3}$ | $-1.9\times10^{-3}$ | $5.4\times10^{-5}$ |
| | 64 | $+1.6\times10^{-4}$ | $+2.0\times10^{-4}$ | $+4.8\times10^{-4}$ | $-5.0\times10^{-4}$ | $-1.0\times10^{-3}$ | $1.6\times10^{-5}$ |
| | 128 | $+8.6\times10^{-5}$ | $+9.9\times10^{-5}$ | $+2.3\times10^{-4}$ | $-2.3\times10^{-4}$ | $-5.2\times10^{-4}$ | $4.4\times10^{-6}$ |
| | order | 0.71, 0.88, 0.94 | 1.07, 1.03, 1.01 | 1.11, 1.05, 1.03 | 1.31, 1.20, 1.11 | 0.82, 0.90, 0.95 | 1.6, 1.8, 1.9 |
| **cubic (fix)** | 16 | $+6.0\times10^{-5}$ | $+6.5\times10^{-5}$ | $+6.2\times10^{-5}$ | $+2.5\times10^{-4}$ | $+2.1\times10^{-4}$ | $1.7\times10^{-4}$ |
| | 32 | $+1.4\times10^{-5}$ | $+1.5\times10^{-5}$ | $+1.5\times10^{-5}$ | $+7.0\times10^{-5}$ | $+6.5\times10^{-5}$ | $5.4\times10^{-5}$ |
| | 64 | $+3.5\times10^{-6}$ | $+3.6\times10^{-6}$ | $+3.6\times10^{-6}$ | $+1.8\times10^{-5}$ | $+1.8\times10^{-5}$ | $1.6\times10^{-5}$ |
| | 128 | $+8.7\times10^{-7}$ | $+8.8\times10^{-7}$ | $+8.8\times10^{-7}$ | $+4.7\times10^{-6}$ | $+4.6\times10^{-6}$ | $4.4\times10^{-6}$ |
| | order | 2.06, 2.02, 2.01 | 2.12, 2.06, 2.03 | 2.07, 2.05, 2.03 | 1.84, 1.93, 1.97 | 1.72, 1.87, 1.94 | 1.6, 1.8, 1.9 |
| lin closure | 64 | $+7.3\times10^{-6}$ | $-2.4\times10^{-6}$ | $+3.6\times10^{-7}$ | $+3.3\times10^{-5}$ | $-2.2\times10^{-6}$ | $1.6\times10^{-5}$ |
| | order | 2.2, 2.1, 2.0 | 1.5, 1.8, 1.9 | 3.1, 2.9, 2.7 | 1.6, 1.8, 1.9 | 2.6, 2.9, 3.1 | |
| W | 64 | $+9.5\times10^{-9}$ | $+1.3\times10^{-9}$ | $-6.5\times10^{-9}$ | $-3.3\times10^{-7}$ | $+2.1\times10^{-7}$ | $4.2\times10^{-9}$ |
| | order | 3.4, 3.2, 3.1 | 4.2, 4.1, 4.1 | 3.5, 3.3, 3.1 | 2.6, 2.8, 2.9 | 2.4, 2.7, 2.9 | 3.0, 3.5, 3.7 |

With the fix the wall faces are second order and equal to the interior offset (top faces $1.8\times10^{-5}$ against the interior maximum $1.6\times10^{-5}$ at $n_z$ 64): the wall error is gone, and the interior faces are bitwise those of the default. W is a different, more accurate scheme (about 4th order) because it also replaces $B$ in the interior.

## 6. Effect on the onset growth rate (linear column, inviscid, cov on; $\sigma/\sigma_c-1$)
`wallfix_growth.py`; tables `runs/wallfix_growth_{1H,3H}.txt`.

| case | 1 H: $n_z$ 16 / 32 / 64 | 3 H: $n_z$ 16 / 32 / 64 |
|---|---|---|
| default | $-1.4\times10^{-4}$ / $-3.6\times10^{-3}$ / $-6.2\times10^{-4}$ | $+2.2\times10^{-2}$ / $-8.6\times10^{-3}$ / $-2.0\times10^{-3}$ |
| wall fix (cubic) | $+4.2\times10^{-2}$ / $+4.3\times10^{-3}$ / $+4.3\times10^{-4}$ | $+4.6\times10^{-2}$ / $+6.5\times10^{-4}$ / $-7.0\times10^{-4}$ |
| wall fix + D | $-6.4\times10^{-3}$ / $-8.4\times10^{-4}$ / $-1.7\times10^{-4}$ | $-3.6\times10^{-2}$ / $-6.3\times10^{-3}$ / $-1.5\times10^{-3}$ |
| W + D | $-3.4\times10^{-3}$ / $-2.0\times10^{-4}$ / $-1.3\times10^{-5}$ | $-4.6\times10^{-3}$ / $-2.9\times10^{-4}$ / $-2.2\times10^{-5}$ |

* The wall fix alone exposes the face-form wall-cell work error (positive, about $\Delta z^3$; D removes it), exactly as W alone does.
* Wall fix + D is cleanly **second order** (order 2.0–2.3) and negative. That is the interior offset $\tfrac{\Delta z^2}{12}(p'R'+2pR'')$ of the default kernel, which the wall fix keeps by design. It grows with depth ($-1.7\times10^{-4}$ at 1 H vs $-1.5\times10^{-3}$ at 3 H, $n_z$ 64).
* So the wall fix turns the default from "first-order wall error partly cancelling a third-order wall-cell work error" into a clean, predictable second-order scheme. W+D removes the interior offset as well and is fourth order.

## 7. With W on: is any second-order term left in the linearised operator? (part 2)
Term by term, in the linear operator of the replica with W+D and cov:

| term | treatment | contribution |
|---|---|---|
| x2 enthalpy covariance $\tfrac{\Delta z^2}{12}\rho u_zh_z$ | cov (exact at linear order; the lead's quadrature ratio 1.000) | removed |
| V: $w=\langle m\rangle/\langle\rho\rangle$ in the x1 mass **and** energy flux | pair: entropy source $-(h_{0,z}+g)\delta F=O(\epsilon)\delta F$ | switching to $\rho w$ reconstruction changes $-2.15\times10^{-5}\to-1.93\times10^{-5}$ (3 H, $n_z$ 64): negligible |
| WB rest face density (interior offset and wall band) | W | $O(\Delta z^4)$ |
| face gravity work, $\tfrac{\Delta z^2}{12}m''$ and the wall cells | D | $O(\Delta z^4)$ |
| LMARS acoustic terms, WENO5 | jumps $O(\Delta z^5)$ | — |
| total, W+D+cov | | $-4.6\times10^{-3}$ / $-2.9\times10^{-4}$ / $-2.2\times10^{-5}$: order 4.0, 3.7 |

There is **no second-order term left** in this operator with W+D on. W without D is $+7.5\times10^{-4}$ (3 H, $n_z$ 64), order about 3.2: the face-form wall-cell work. The second-order onset error that snapy shows with W+D on (3 H, $n_z$ 64: $+6.4\times10^{-3}$) is therefore the term $X$ of `docs/onset-wb-ref4.md` §3. It is W/D-independent, $\propto\Delta z^2/\epsilon$ and destabilising, and absent from this operator. The next step remains snapy's own Jacobian on the 3 H, $n_z$ 32 deck, diffed row by row against the replica's.
