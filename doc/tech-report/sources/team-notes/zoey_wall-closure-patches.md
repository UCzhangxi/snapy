# Wall-closure patches 37dce4e..ac4dc56 (snapy)

Three local commits, oldest first, made with `git format-patch 37dce4e..ac4dc56`, one file per commit. All are authored by Zoey Hu <hzin@umich.edu>, with no AI-attribution trailers. Nothing was pushed.

| file | commit | subject | bytes | sha256 |
|---|---|---|---|---|
| `0001-Default-x1-reference-continue-rho-p-linearly-past-a-.patch` | `024d5371921d340c7a0dbf675307e3ca4a2d349c` | Default x1 reference: continue rho/p linearly past a clamped wall | 33921 | `5dab8200c773a20c3aa01ea5909fd0ecc9c942838fb3aa2c7fe0fcb8f9a1bf8f` |
| `0002-Default-x1-reference-continue-ln-rho-p-not-rho-p-pas.patch` | `0e82f76eac4964b522e68856e9c45f683bd145cb` | Default x1 reference: continue ln(rho/p), not rho/p, past a clamped wall | 21376 | `069ba2f05634a35efb0ac7d5fdb305d325c13d42d9928d355ad58224f98f90af` |
| `0003-Default-x1-reference-wall-continuation-linear-where-.patch` | `ac4dc5686a6a2062dec90285f45130ef29802b41` | Default x1 reference: wall continuation linear where rho/p falls, ln where it rises | 27106 | `3dae31b84e8f4232484a7f8af282b4d3c2c62f7d1e4c747d06d68a339068dc2f` |

- Base: `37dce4efdd8b1bdf9f08a91edf8fd3da38384672` (tree `708c4e71`).
- **ac4dc56:** commit `ac4dc5686a6a2062dec90285f45130ef29802b41`, tree `3e4ccef266777d38db8335e57bb1164cc3999e4f`.
- **`git am` check:** in a scratch worktree at 37dce4e, `git am` applied all three patches cleanly (exit 0, no fuzz or conflicts).
  - The resulting trees are `a52f1633…`, `2835e22d…` and `3e4ccef266777d38db8335e57bb1164cc3999e4f`.
  - They are identical to the trees of 024d537, 0e82f76 and ac4dc56. The final HEAD^{tree} equals ac4dc56's tree.
  - The applied commits get new shas, because the committer and date change; the content is identical. The scratch worktree has been removed.
- **Saving a patch back:** copy everything between a block's opening ```` ```diff ```` line and its closing ```` ``` ```` line, and add one trailing newline (each patch ends with git's version line followed by a blank line). The bytes then match the sha256 above. None of the patches contains a backtick fence.

## 0001-Default-x1-reference-continue-rho-p-linearly-past-a-.patch

```diff
From 024d5371921d340c7a0dbf675307e3ca4a2d349c Mon Sep 17 00:00:00 2001
From: Zoey Hu <hzin@umich.edu>
Date: Fri, 9 Oct 2026 20:02:19 -0400
Subject: [PATCH 1/3] Default x1 reference: continue rho/p linearly past a
 clamped wall

With SNAP_WB_REF4 off, hydro_ref_x1_rop_smooth repeated the wall cell for
every binomial index past a clamped physical wall. That is exact only for a
constant rho/p: on a stratified column the wall cells' smoothed ratio is off
by 3/8 and 1/16 of a cell's change, and the face density reference at the
first three faces is O(dz) (7/32 of a cell's change at the first face above
the wall), against O(dz^2) elsewhere. The even-parity perturbation ghosts
then carry that bias into the solver's face densities.

Past a clamped wall that owns at least two cells, the stencil now continues
rho/p linearly from the two cells next to the wall (r_-k = r_0 + k (r_0 -
r_1)), falling back to the wall cell where that is not positive. The binomial
reproduces a linear profile, so the wall cells and faces keep the interior's
second order. The MPS tensor path follows the same rule (not run here).
Derivation: docs/derivations/wb-ref-wall.md.

Polytrope T = 1 - z/2, one pressure scale height, exact cell averages
(test_wb_ref_wall): the face density reference at the first face above the
bottom wall goes 2.88e-3 / 1.39e-3 -> 1.57e-4 / 3.87e-5 at nz 32 / 64
(order 1.05 -> 2.02); the solver's rho_L there 5.21e-4 / 2.54e-4 -> 3.58e-5 /
8.65e-6. Only the face reference at faces 0-2 and the cell reference at
cells 0-1 next to each clamped wall change; psf, pref and every other face
and cell are bitwise unchanged (nz 16-128), and an isothermal column is
unchanged everywhere. test_wb_ref_wall fails at 37dce4e (wall-face orders
0.74-1.31) and passes here.
---
 docs/derivations/wb-ref-wall.md  | 119 ++++++++++++++
 docs/derivations/wb-ref-wall.tex | 153 ++++++++++++++++++
 src/hydro/hydro_dispatch.cpp     |  32 +++-
 src/hydro/hydro_ref_x1_impl.h    |  39 ++++-
 tests/CMakeLists.txt             |   1 +
 tests/test_wb_ref_wall.cpp       | 270 +++++++++++++++++++++++++++++++
 6 files changed, 601 insertions(+), 13 deletions(-)
 create mode 100644 docs/derivations/wb-ref-wall.md
 create mode 100644 docs/derivations/wb-ref-wall.tex
 create mode 100644 tests/test_wb_ref_wall.cpp

diff --git a/docs/derivations/wb-ref-wall.md b/docs/derivations/wb-ref-wall.md
new file mode 100644
index 0000000..452b77f
--- /dev/null
+++ b/docs/derivations/wb-ref-wall.md
@@ -0,0 +1,119 @@
+# The default well-balanced x1 reference at a physical wall
+
+This is the default reference, with `SNAP_WB_REF4` off and `dynamics/wb-wall-clamp` on (the default). With the
+repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
+wall, against $O(\Delta z^2)$ elsewhere. A linear continuation of $\rho/p$ past the wall restores the interior
+order there and leaves every other face bit for bit. The code is `src/hydro/hydro_ref_x1_impl.h`
+(`hydro_ref_x1_rop_smooth`, `hydro_ref_x1_cell_impl`), with the tensor (MPS) path in
+`src/hydro/hydro_dispatch.cpp`. The test is `tests/test_wb_ref_wall.cpp`.
+
+## 1. What the kernel builds
+
+Per column, with $r_i = \bar\rho_i/\bar p_i$ and the binomial $B = (1, 4, 6, 4, 1)/16$:
+
+$$
+r^s_i = \sum_{m=-2}^{2} B_m\, r_{i+m},\qquad
+\rho_{{\rm ref},i} = p_{{\rm ref},i}\, r^s_i,\qquad
+\rho_{{\rm sf},f} = p_{{\rm sf},f}\,\tfrac12\big(r^s_{f-1} + r^s_f\big),
+$$
+
+where face $f$ is the lower face of cell $f$. The solver's face density is $\rho_{\rm sf} + \mathcal W[\bar\rho -
+\rho_{\rm ref}]$, where $\mathcal W$ is WENO5 and the perturbation's ghosts at a wall are filled with even parity
+(`hydro_forward.cpp`). At 37dce4e:
+- the clamp is at `hydro_ref_x1_impl.h:74`: an index past the wall is replaced by the wall cell;
+- `jlo`/`jhi` are set at `:159-160`;
+- $r^s$, $\rho_{\rm ref}$ and $\rho_{\rm sf}$ are formed at `:161-167`;
+- the even-parity fill is at `hydro_forward.cpp:276-292`.
+
+## 2. Interior order
+
+For smooth $r$, $B$ has unit sum, zero first moment and second moment 1 (in cells), so $r^s_i = r_i +
+\tfrac{\Delta z^2}{2} r''_i + O(\Delta z^4)$. The mean of two neighbouring cells adds $\tfrac{\Delta z^2}{8}r''$.
+With $p_{{\rm sf},f} = p(z_f)$ from the scan, and $r_i = R_i + O(\Delta z^2)$ for a ratio of averages,
+
+$$
+\rho_{{\rm sf},f} = \rho(z_f) + O(\Delta z^2)\qquad\text{(interior faces)}.
+$$
+
+## 3. The repeated wall cell is first order
+
+Near the bottom wall, write $r_j = r_0 + j\,a + O(\Delta z^2)$ with $a = r'\Delta z = O(\Delta z)$, and index the
+cells from the wall, $j = 0, 1, \dots$. Repeating $r_0$ for every $j < 0$ gives:
+
+- wall cell: $r^s_0 = (11 r_0 + 4 r_1 + r_2)/16 = r_0 + \tfrac{3}{8}a$;
+- next cell: $r^s_1 = (5 r_0 + 6 r_1 + 4 r_2 + r_3)/16 = r_1 + \tfrac{1}{16}a$;
+- first ghost (it enters the wall face): $r^s_{-1} = r_0 + \tfrac{1}{16}a$, where the true value is $r_0 - a$.
+
+Against the true face values $r(z_f)$, the face references are off by:
+
+| face (cells from the wall) | error of $\tfrac12(r^s_{f-1}+r^s_f)$ |
+|---|---|
+| 0 (the wall face) | $\tfrac{23}{32}a$ |
+| 1 | $\tfrac{7}{32}a$ |
+| 2 | $\tfrac{1}{32}a$ |
+| $\ge 3$ | $O(\Delta z^2)$ |
+
+At the top wall the signs flip. Relative to $r$ the error is a fixed multiple of $(r'/r)\Delta z$, so it is
+**first order**. It vanishes when $r' = 0$, so an isothermal column has no wall error.
+
+Check against the test column (polytrope $T = 1 - \beta z$, $\beta = 0.5$, one pressure scale height, nz 64,
+$\Delta z = 0.01230$; $r'/r = \beta/T$). The prediction at face 1 is $\tfrac{7}{32}\cdot0.5\cdot0.0123 = 1.35\times10^{-3}$,
+and `test_wb_ref_wall` measures $1.39\times10^{-3}$. At face 2 the prediction is $1.9\times10^{-4}$ plus the
+interior $O(\Delta z^2)$ part; it measures $2.5\times10^{-4}$.
+
+**The even-parity ghosts.** $\rho' = \bar\rho - \rho_{\rm ref}$ inherits the wall bias,
+$-\tfrac38 a\,p$ in the wall cell and $-\tfrac1{16}a\,p$ in the next. The even mirror carries that $O(\Delta z)$
+feature into the ghosts, so $\mathcal W[\rho']$ does not cancel it, and the solver's face densities $\rho_{L,R}$ at
+faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times10^{-4}$, then $-2.5\times10^{-4}$ at nz 32, 64).
+The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
+only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.
+
+## 4. The closure: continue $\rho/p$ linearly past the wall
+
+Past a clamped wall, take
+
+$$
+r_{-k} = r_0 + k\,(r_0 - r_1),\qquad k = 1, 2, 3
+$$
+
+(and the mirror image at the top), in place of $r_0$. $B$ reproduces a linear profile exactly, so the $O(a)$
+terms above cancel. What remains is the continuation's own curvature error, $\tfrac{k(k+1)}{2}r''\Delta z^2$, which is
+$O(\Delta z^2)$. The wall cells, and faces 0–2, then have the interior's order. For constant $r$ the continuation
+equals $r_0$ exactly, so an isothermal column is unchanged bit for bit.
+
+Guards (the clamp stays):
+- the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
+  `test_hydro_ref_x1` hold;
+- a continuation that is not positive falls back to $r_0$.
+
+Measured with `test_wb_ref_wall`, $\beta = 0.5$, dsf at face 1:
+
+| nz | before | after |
+|---|---|---|
+| 16 | $6.16\times10^{-3}$ | $6.48\times10^{-4}$ |
+| 32 | $2.88\times10^{-3}$ | $1.57\times10^{-4}$ |
+| 64 | $1.39\times10^{-3}$ | $3.87\times10^{-5}$ |
+| 128 | $6.84\times10^{-4}$ | $9.78\times10^{-6}$ |
+
+The observed order goes from about 1.05 to about 2.0. The solver's $\rho_L$ at face 1 goes from
+$-2.54\times10^{-4}$ (nz 64) to $8.6\times10^{-6}$. Faces 1–2 at both walls now stay at or below the largest
+interior error ($1.45\times10^{-4}$ at nz 64).
+
+**What changes.** At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
+plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
+(compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
+`wb-ref4.md`), so `balance_column` and the discrete rest state are unchanged.
+
+**Why linear, and why not the `SNAP_WB_REF4` closure.**
+- The default reference is second order, so a two-point continuation is enough.
+- It needs only two owned cells and amplifies cell-to-cell noise the least. Its largest weight is $1+k$, against
+  10–20 for a cubic.
+- `SNAP_WB_REF4`'s wall closure (`wb_ref4.cpp`) is a post-pass that replaces $\rho_{\rm ref}$ with
+  $p_{\rm ref}F(r)$ and $\rho_{\rm sf}$ with a fourth-order face value on *every* face, so applying it would change
+  every interior face. Its cubic continuation is tied to $F$: $F$ with the cubic values returns $r$ at the end
+  cells exactly. It also needs four owned cells.
+- A cubic (or quadratic) continuation inside $B$ would also restore second order. It was not chosen for the
+  reasons above.
+
+**Not covered.** Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
+is changed to the same rule but was not run here, since there is no MPS device.
diff --git a/docs/derivations/wb-ref-wall.tex b/docs/derivations/wb-ref-wall.tex
new file mode 100644
index 0000000..d342c8e
--- /dev/null
+++ b/docs/derivations/wb-ref-wall.tex
@@ -0,0 +1,153 @@
+% GENERATED FROM wb-ref-wall.md BY md2tex.py -- DO NOT HAND-EDIT.
+\documentclass[11pt,a4paper]{article}
+\usepackage[margin=1in]{geometry}
+\usepackage{amsmath,amssymb,bm}
+\usepackage{listings}
+\usepackage[hidelinks]{hyperref}
+\usepackage{longtable}
+\usepackage{booktabs}
+\setlength{\parskip}{0.6em}
+\setlength{\parindent}{0pt}
+\lstset{basicstyle=\ttfamily\footnotesize,breaklines=true,frame=single,
+        columns=fullflexible,keepspaces=true}
+\title{The default well-balanced x1 reference at a physical wall}
+\author{snapy --- derivation}\date{}
+\begin{document}
+\maketitle
+\section*{The default well-balanced x1 reference at a physical wall}
+
+This is the default reference, with \texttt{SNAP\_WB\_REF4} off and \texttt{dynamics/wb-wall-clamp} on (the default). With the
+repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
+wall, against $O(\Delta z^2)$ elsewhere. A linear continuation of $\rho/p$ past the wall restores the interior
+order there and leaves every other face bit for bit. The code is \texttt{src/hydro/hydro\_ref\_x1\_impl.h}
+(\texttt{hydro\_ref\_x1\_rop\_smooth}, \texttt{hydro\_ref\_x1\_cell\_impl}), with the tensor (MPS) path in
+\texttt{src/hydro/hydro\_dispatch.cpp}. The test is \texttt{tests/test\_wb\_ref\_wall.cpp}.
+
+\section*{1. What the kernel builds}
+
+Per column, with $r_i = \bar\rho_i/\bar p_i$ and the binomial $B = (1, 4, 6, 4, 1)/16$:
+
+\begin{equation*}
+r^s_i = \sum_{m=-2}^{2} B_m\, r_{i+m},\qquad
+\rho_{{\rm ref},i} = p_{{\rm ref},i}\, r^s_i,\qquad
+\rho_{{\rm sf},f} = p_{{\rm sf},f}\,\tfrac12\big(r^s_{f-1} + r^s_f\big),
+\end{equation*}
+
+where face $f$ is the lower face of cell $f$. The solver's face density is $\rho_{\rm sf} + \mathcal W[\bar\rho -$
+\textbackslash\{\}rho\_\{\textbackslash\{\}rm ref\}]$, where $\textbackslash\{\}mathcal W$ is WENO5 and the perturbation's ghosts at a wall are filled with even parity$
+(\texttt{hydro\_forward.cpp}). At 37dce4e:
+\begin{itemize}
+\item the clamp is at \texttt{hydro\_ref\_x1\_impl.h:74}: an index past the wall is replaced by the wall cell;
+\item \texttt{jlo}/\texttt{jhi} are set at \texttt{:159-160};
+\item $r^s$, $\rho_{\rm ref}$ and $\rho_{\rm sf}$ are formed at \texttt{:161-167};
+\item the even-parity fill is at \texttt{hydro\_forward.cpp:276-292}.
+\end{itemize}
+
+\section*{2. Interior order}
+
+For smooth $r$, $B$ has unit sum, zero first moment and second moment 1 (in cells), so $r^s_i = r_i +$
+\textbackslash\{\}tfrac\{\textbackslash\{\}Delta z\textasciicircum{}2\}\{2\} r''\_i + O(\textbackslash\{\}Delta z\textasciicircum{}4)$. The mean of two neighbouring cells adds $\textbackslash\{\}tfrac\{\textbackslash\{\}Delta z\textasciicircum{}2\}\{8\}r''$.$
+With $p_{{\rm sf},f} = p(z_f)$ from the scan, and $r_i = R_i + O(\Delta z^2)$ for a ratio of averages,
+
+\begin{equation*}
+\rho_{{\rm sf},f} = \rho(z_f) + O(\Delta z^2)\qquad\text{(interior faces)}.
+\end{equation*}
+
+\section*{3. The repeated wall cell is first order}
+
+Near the bottom wall, write $r_j = r_0 + j\,a + O(\Delta z^2)$ with $a = r'\Delta z = O(\Delta z)$, and index the
+cells from the wall, $j = 0, 1, \dots$. Repeating $r_0$ for every $j < 0$ gives:
+
+\begin{itemize}
+\item wall cell: $r^s_0 = (11 r_0 + 4 r_1 + r_2)/16 = r_0 + \tfrac{3}{8}a$;
+\item next cell: $r^s_1 = (5 r_0 + 6 r_1 + 4 r_2 + r_3)/16 = r_1 + \tfrac{1}{16}a$;
+\item first ghost (it enters the wall face): $r^s_{-1} = r_0 + \tfrac{1}{16}a$, where the true value is $r_0 - a$.
+\end{itemize}
+
+Against the true face values $r(z_f)$, the face references are off by:
+
+\begin{longtable}{ll}
+\toprule
+face (cells from the wall) & error of $\tfrac12(r^s_{f-1}+r^s_f)$ \\
+\midrule
+0 (the wall face) & $\tfrac{23}{32}a$ \\
+1 & $\tfrac{7}{32}a$ \\
+2 & $\tfrac{1}{32}a$ \\
+$\ge 3$ & $O(\Delta z^2)$ \\
+\bottomrule
+\end{longtable}
+
+At the top wall the signs flip. Relative to $r$ the error is a fixed multiple of $(r'/r)\Delta z$, so it is
+\textbf{first order}. It vanishes when $r' = 0$, so an isothermal column has no wall error.
+
+Check against the test column (polytrope $T = 1 - \beta z$, $\beta = 0.5$, one pressure scale height, nz 64,
+$\Delta z = 0.01230$; $r'/r = \beta/T$). The prediction at face 1 is $\tfrac{7}{32}\cdot0.5\cdot0.0123 = 1.35\times10^{-3}$,
+and \texttt{test\_wb\_ref\_wall} measures $1.39\times10^{-3}$. At face 2 the prediction is $1.9\times10^{-4}$ plus the
+interior $O(\Delta z^2)$ part; it measures $2.5\times10^{-4}$.
+
+\textbf{The even-parity ghosts.} $\rho' = \bar\rho - \rho_{\rm ref}$ inherits the wall bias,
+$-\tfrac38 a\,p$ in the wall cell and $-\tfrac1{16}a\,p$ in the next. The even mirror carries that $O(\Delta z)$
+feature into the ghosts, so $\mathcal W[\rho']$ does not cancel it, and the solver's face densities $\rho_{L,R}$ at
+faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times10^{-4}$, then $-2.5\times10^{-4}$ at nz 32, 64).
+The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
+only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.
+
+\section*{4. The closure: continue $\rho/p$ linearly past the wall}
+
+Past a clamped wall, take
+
+\begin{equation*}
+r_{-k} = r_0 + k\,(r_0 - r_1),\qquad k = 1, 2, 3
+\end{equation*}
+
+(and the mirror image at the top), in place of $r_0$. $B$ reproduces a linear profile exactly, so the $O(a)$
+terms above cancel. What remains is the continuation's own curvature error, $\tfrac{k(k+1)}{2}r''\Delta z^2$, which is
+$O(\Delta z^2)$. The wall cells, and faces 0–2, then have the interior's order. For constant $r$ the continuation
+equals $r_0$ exactly, so an isothermal column is unchanged bit for bit.
+
+Guards (the clamp stays):
+\begin{itemize}
+\item the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
+  \texttt{test\_hydro\_ref\_x1} hold;
+\item a continuation that is not positive falls back to $r_0$.
+\end{itemize}
+
+Measured with \texttt{test\_wb\_ref\_wall}, $\beta = 0.5$, dsf at face 1:
+
+\begin{longtable}{lll}
+\toprule
+nz & before & after \\
+\midrule
+16 & $6.16\times10^{-3}$ & $6.48\times10^{-4}$ \\
+32 & $2.88\times10^{-3}$ & $1.57\times10^{-4}$ \\
+64 & $1.39\times10^{-3}$ & $3.87\times10^{-5}$ \\
+128 & $6.84\times10^{-4}$ & $9.78\times10^{-6}$ \\
+\bottomrule
+\end{longtable}
+
+The observed order goes from about 1.05 to about 2.0. The solver's $\rho_L$ at face 1 goes from
+$-2.54\times10^{-4}$ (nz 64) to $8.6\times10^{-6}$. Faces 1–2 at both walls now stay at or below the largest
+interior error ($1.45\times10^{-4}$ at nz 64).
+
+\textbf{What changes.} At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
+plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
+(compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
+\texttt{wb-ref4.md}), so \texttt{balance\_column} and the discrete rest state are unchanged.
+
+\textbf{Why linear, and why not the \texttt{SNAP\_WB\_REF4} closure.}
+\begin{itemize}
+\item The default reference is second order, so a two-point continuation is enough.
+\item It needs only two owned cells and amplifies cell-to-cell noise the least. Its largest weight is $1+k$, against
+  10–20 for a cubic.
+\item \texttt{SNAP\_WB\_REF4}'s wall closure (\texttt{wb\_ref4.cpp}) is a post-pass that replaces $\rho_{\rm ref}$ with
+  $p_{\rm ref}F(r)$ and $\rho_{\rm sf}$ with a fourth-order face value on *every* face, so applying it would change
+  every interior face. Its cubic continuation is tied to $F$: $F$ with the cubic values returns $r$ at the end
+  cells exactly. It also needs four owned cells.
+\item A cubic (or quadratic) continuation inside $B$ would also restore second order. It was not chosen for the
+  reasons above.
+\end{itemize}
+
+\textbf{Not covered.} Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
+is changed to the same rule but was not run here, since there is no MPS device.
+
+\end{document}
diff --git a/src/hydro/hydro_dispatch.cpp b/src/hydro/hydro_dispatch.cpp
index 95c29e4..f6ed166 100644
--- a/src/hydro/hydro_dispatch.cpp
+++ b/src/hydro/hydro_dispatch.cpp
@@ -157,16 +157,34 @@ void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
   }

   auto rop = (rho / w[IPR]).clone();
-  if (wall_clamp && phys_in) {  // clamp the smoothing to interior cells
-    rop.narrow(-1, 0, il).copy_(rop.narrow(-1, il, 1).expand({-1, -1, il}));
-  }
-  if (wall_clamp && phys_out) {
-    rop.narrow(-1, iu + 1, nc1 - 1 - iu)
-        .copy_(rop.narrow(-1, iu, 1).expand({-1, -1, nc1 - 1 - iu}));
-  }
   auto lo_edge = rop.narrow(-1, 0, 1);
   auto hi_edge = rop.narrow(-1, nc1 - 1, 1);
   auto pad = torch::cat({lo_edge, lo_edge, rop, hi_edge, hi_edge}, -1);
+  // past a clamped wall: rho/p continued linearly from the two cells next to
+  // it where positive, else the wall cell (hydro_ref_x1_rop_smooth); pad
+  // index p holds cell p - 2
+  if (wall_clamp && phys_in) {
+    auto r0 = rop.narrow(-1, il, 1);
+    for (int j = -2; j < il; ++j) {
+      auto v = r0;
+      if (il + 1 <= iu) {
+        auto e = r0 + double(il - j) * (r0 - rop.narrow(-1, il + 1, 1));
+        v = torch::where(e > 0., e, r0);
+      }
+      pad.narrow(-1, j + 2, 1).copy_(v);
+    }
+  }
+  if (wall_clamp && phys_out) {
+    auto r0 = rop.narrow(-1, iu, 1);
+    for (int j = iu + 1; j < nc1 + 2; ++j) {
+      auto v = r0;
+      if (iu - 1 >= il) {
+        auto e = r0 + double(j - iu) * (r0 - rop.narrow(-1, iu - 1, 1));
+        v = torch::where(e > 0., e, r0);
+      }
+      pad.narrow(-1, j + 2, 1).copy_(v);
+    }
+  }
   auto rs = (pad.narrow(-1, 0, nc1) + 4. * pad.narrow(-1, 1, nc1) +
              6. * pad.narrow(-1, 2, nc1) + 4. * pad.narrow(-1, 3, nc1) +
              pad.narrow(-1, 4, nc1)) /
diff --git a/src/hydro/hydro_ref_x1_impl.h b/src/hydro/hydro_ref_x1_impl.h
index a4c4906..e2f51ec 100644
--- a/src/hydro/hydro_ref_x1_impl.h
+++ b/src/hydro/hydro_ref_x1_impl.h
@@ -59,20 +59,44 @@ inline DISPATCH_MACRO void hydro_ref_x1_scan_impl(T const* w, T const* dx1f,
   }
 }

-//! rho/p smoothed by a clamped 5-point binomial along x1: the reference must
+//! rho/p smoothed by a 5-point binomial along x1: the reference must
 //! track the column profile at LARGE scales only. An unsmoothed local rho/p
 //! makes rho' degenerate with the pressure perturbation, so entropy/buoyancy
 //! anomalies bypass the high-order reconstruction; a bottom-anchored
 //! isentrope reference errs by orders of magnitude on a stratified column.
+//! Past a clamped wall (ext_lo/ext_hi: the wall side owns at least two cells)
+//! the stencil continues rho/p linearly from the two cells next to the wall
+//! instead of repeating the wall cell. The binomial reproduces a linear profile
+//! exactly, so the wall cells keep the interior's O(dz^2) bias; a repeated wall
+//! cell is exact only for constant rho/p and leaves an O(dz) error at the
+//! first faces (docs/derivations/wb-ref-wall.md). A continuation that is not
+//! positive falls back to the wall cell. Only owned cells are read.
 template <typename T>
 inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
                                                 int flat, int nc1, int i,
-                                                int jlo, int jhi) {
+                                                int jlo, int jhi, bool ext_lo,
+                                                bool ext_hi) {
+  auto rop = [&](int j) {
+    return w[IDN * ncells + flat + j] / w[IPR * ncells + flat + j];
+  };
   T v[5];
   for (int m = -2; m <= 2; ++m) {
     int j = i + m;
-    j = j < jlo ? jlo : (j > jhi ? jhi : j);
-    v[m + 2] = w[IDN * ncells + flat + j] / w[IPR * ncells + flat + j];
+    if (j < jlo) {
+      v[m + 2] = rop(jlo);
+      if (ext_lo) {
+        T e = v[m + 2] + T(jlo - j) * (v[m + 2] - rop(jlo + 1));
+        if (e > T(0)) v[m + 2] = e;
+      }
+    } else if (j > jhi) {
+      v[m + 2] = rop(jhi);
+      if (ext_hi) {
+        T e = v[m + 2] + T(j - jhi) * (v[m + 2] - rop(jhi - 1));
+        if (e > T(0)) v[m + 2] = e;
+      }
+    } else {
+      v[m + 2] = rop(j);
+    }
   }
   return (v[0] + T(4) * v[1] + T(6) * v[2] + T(4) * v[3] + v[4]) / T(16);
 }
@@ -158,9 +182,12 @@ inline DISPATCH_MACRO void hydro_ref_x1_cell_impl(
   pref[flat + i] = cell_pref;
   int jlo = (wall_clamp && phys_in) ? il : 0;
   int jhi = (wall_clamp && phys_out) ? iu : nc1 - 1;
-  T rs = hydro_ref_x1_rop_smooth(w, ncells, flat, nc1, i, jlo, jhi);
+  bool ext_lo = wall_clamp && phys_in && il + 1 <= iu;
+  bool ext_hi = wall_clamp && phys_out && iu - 1 >= il;
+  T rs = hydro_ref_x1_rop_smooth(w, ncells, flat, nc1, i, jlo, jhi, ext_lo,
+                                 ext_hi);
   T rf = i > 0 ? T(0.5) * (hydro_ref_x1_rop_smooth(w, ncells, flat, nc1, i - 1,
-                                                   jlo, jhi) +
+                                                   jlo, jhi, ext_lo, ext_hi) +
                            rs)
                : rs;
   dref[flat + i] = cell_pref * rs;
diff --git a/tests/CMakeLists.txt b/tests/CMakeLists.txt
index e58404d..628aa87 100644
--- a/tests/CMakeLists.txt
+++ b/tests/CMakeLists.txt
@@ -56,6 +56,7 @@ seam_arm(_wb_ref4 "SNAP_WB_REF4=1"
          wb_ref4_flag_at_the_seam_split_matches_one_block)
 setup_test(test_wb_wall_corner)
 setup_test(test_face_floor)
+setup_test(test_wb_ref_wall)
 # #289: these two pin values of the kernel's x1 reference; run them again with
 # SNAP_WB_REF4 set, where each checks the switched reference instead
 foreach(_t test_balance_column test_face_floor)
diff --git a/tests/test_wb_ref_wall.cpp b/tests/test_wb_ref_wall.cpp
new file mode 100644
index 0000000..771a252
--- /dev/null
+++ b/tests/test_wb_ref_wall.cpp
@@ -0,0 +1,270 @@
+// C/C++
+#include <unistd.h>
+
+#include <cmath>
+#include <cstdio>
+#include <cstdlib>
+#include <fstream>
+#include <string>
+#include <tuple>
+#include <vector>
+
+// external
+#include <gtest/gtest.h>
+
+#include "cuda_test_gate.hpp"
+
+// torch
+#include <torch/torch.h>
+
+// snap
+#include <snap/snap.h>
+
+#include <snap/hydro/hydro.hpp>
+#include <snap/hydro/hydro_dispatch.hpp>
+#include <snap/mesh/meshblock.hpp>
+
+using namespace snap;
+
+// The default (SNAP_WB_REF4 off) well-balanced x1 reference at a physical
+// wall. A hydrostatic polytrope T = 1 - beta z (g = R = 1, rho = p / T) one
+// pressure scale height deep, reflecting x1 walls, held as exact cell
+// averages. Reported per face f, relative to the exact rho(z_f):
+//   dsf          the face density reference itself;
+//   rho_L, rho_R the face densities the solver builds from it,
+//                dsf + WENO5(rho - dref) with the even-parity wall ghosts of
+//                hydro_forward.cpp.
+// Interior faces are O(dz^2). See docs/derivations/wb-ref-wall.md.
+
+namespace {
+
+constexpr int kNg = 3;
+constexpr int kDim1 = 3;  // x1, as DIM1 in hydro_forward.cpp
+
+struct Profile {
+  double beta;            // T = 1 - beta z; beta = 0: isothermal
+  double depth() const {  // ln(p_b / p_t) = 1
+    return beta == 0. ? 1. : (1. - std::exp(-beta)) / beta;
+  }
+  double p(double z) const {
+    return beta == 0. ? std::exp(-z) : std::pow(1. - beta * z, 1. / beta);
+  }
+  double rho(double z) const { return p(z) / (1. - beta * z); }
+};
+
+std::shared_ptr<MeshBlockImpl> make_block(int nx1, double depth,
+                                          torch::Device device) {
+  char fname[] = "/tmp/test_wb_ref_wall_XXXXXX";
+  int fd = mkstemp(fname);
+  EXPECT_GE(fd, 0);
+  close(fd);
+  std::ofstream(fname) << "reference-state: {Tref: 300., Pref: 1.e5}\n"
+                          "species:\n"
+                          "  - name: dry\n"
+                          "    composition: {O: 0.42, N: 1.56, Ar: 0.01}\n"
+                          "    cv_R: 2.5\n"
+                          "geometry:\n"
+                          "  type: cartesian\n"
+                          "  bounds: {x1min: 0., x1max: "
+                       << depth
+                       << ", x2min: 0., x2max: 1., x3min: 0., x3max: 1.}\n"
+                          "  cells: {nx1: "
+                       << nx1
+                       << ", nx2: 1, nx3: 1, nghost: 3}\n"
+                          "dynamics:\n"
+                          "  equation-of-state: {type: ideal-gas}\n"
+                          "  reconstruct:\n"
+                          "    vertical: {type: weno5, scale: false, shock: "
+                          "false}\n"
+                          "    horizontal: {type: weno5, scale: false, shock: "
+                          "false}\n"
+                          "boundary-condition:\n"
+                          "  external: {x1-inner: reflecting, x1-outer: "
+                          "reflecting}\n";
+  auto options = MeshBlockOptionsImpl::from_yaml(fname);
+  std::remove(fname);
+  auto block = std::make_shared<MeshBlockImpl>(options);
+  block->to(device, torch::kFloat64);
+  return block;
+}
+
+struct Faces {
+  torch::Tensor dsf, rl, rr;  // relative errors at faces il..iu+1
+  double dz;
+};
+
+Faces face_errors(int nx1, Profile const& prof,
+                  torch::Device device = torch::kCPU) {
+  double depth = prof.depth();
+  auto block = make_block(nx1, depth, device);
+  auto coord = block->pcoord;
+  int il = coord->il(), iu = coord->iu(), nc1 = coord->options->nc1();
+  double dz = depth / nx1;
+
+  // exact cell averages (8-point Gauss-Legendre per cell); the ghosts carry
+  // the even mirror a reflecting wall writes
+  static const double gx[4] = {0.1834346424956498, 0.5255324099163290,
+                               0.7966664774136267, 0.9602898564975363};
+  static const double gw[4] = {0.3626837833783620, 0.3137066458778873,
+                               0.2223810344533745, 0.1012285362903763};
+  auto opt = torch::TensorOptions().dtype(torch::kFloat64);
+  auto w = torch::zeros({block->phydro->peos->nvar(), 1, 1, nc1}, opt);
+  auto rho_t = w[IDN], prs_t = w[IPR];
+  auto rho = rho_t.accessor<double, 3>();
+  auto prs = prs_t.accessor<double, 3>();
+  for (int i = il; i <= iu; ++i) {
+    double c = (i - il + 0.5) * dz, h = 0.5 * dz, sr = 0., sp = 0.;
+    for (int k = 0; k < 4; ++k)
+      for (double s : {-1., 1.}) {
+        sr += 0.5 * gw[k] * prof.rho(c + s * gx[k] * h);
+        sp += 0.5 * gw[k] * prof.p(c + s * gx[k] * h);
+      }
+    rho[0][0][i] = sr;
+    prs[0][0][i] = sp;
+  }
+  for (int m = 0; m < kNg; ++m) {
+    for (auto a : {rho, prs}) {
+      a[0][0][il - 1 - m] = a[0][0][il + m];
+      a[0][0][iu + 1 + m] = a[0][0][iu - m];
+    }
+  }
+
+  // the reference, as HydroImpl::_hydro_ref_x1 builds it for one block with
+  // two physical walls (wb-wall-clamp is on by default)
+  w = w.to(device);
+  opt = opt.device(device);
+  auto sizes = w.sizes().slice(1).vec();
+  auto psf_lo = torch::empty(sizes, opt), psf_hi = torch::empty(sizes, opt),
+       pref = torch::empty(sizes, opt), dsf = torch::empty(sizes, opt),
+       dref = torch::empty(sizes, opt);
+  at::native::call_hydro_ref_x1(device.type(), w, coord->dx1f.contiguous(),
+                                torch::Tensor(), psf_lo, psf_hi, pref, dsf,
+                                dref, iu, /*grav=*/1., /*uniform=*/true,
+                                /*phys_in=*/true, /*phys_out=*/true,
+                                /*wall_clamp=*/true);
+
+  // the solver's face densities (hydro_forward.cpp): reconstruct rho - dref
+  // with even-parity wall ghosts, then add dsf back
+  auto wp = w.clone();
+  wp[IPR] -= pref;
+  wp[IDN] -= dref;
+  for (int c : {(int)IPR, (int)IDN}) {
+    wp[c].narrow(-1, il - kNg, kNg).copy_(wp[c].narrow(-1, il, kNg).flip(-1));
+    wp[c]
+        .narrow(-1, iu + 1, kNg)
+        .copy_(wp[c].narrow(-1, iu + 1 - kNg, kNg).flip(-1));
+  }
+  auto wtmp = block->phydro->precon1->forward(wp, kDim1, /*floor=*/false);
+
+  if (char const* path = std::getenv("WB_REF_WALL_DUMP")) {  // review aid
+    std::FILE* fp = std::fopen(path, "ab");
+    for (auto t : {psf_lo, pref, dsf, dref}) {
+      auto c = t.flatten().cpu().contiguous();
+      std::fwrite(c.data_ptr<double>(), sizeof(double), c.numel(), fp);
+    }
+    std::fclose(fp);
+  }
+
+  int nf = iu + 2 - il;
+  auto exact = torch::empty({nf}, torch::kFloat64);
+  for (int f = 0; f < nf; ++f) exact[f] = prof.rho(f * dz);
+  auto at = [&](torch::Tensor t) {
+    return t.flatten().narrow(0, il, nf).cpu();
+  };
+  Faces out;
+  out.dsf = at(dsf) / exact - 1.;
+  out.rl = (at(wtmp[ILT][IDN]) + at(dsf)) / exact - 1.;
+  out.rr = (at(wtmp[IRT][IDN]) + at(dsf)) / exact - 1.;
+  out.dz = dz;
+  return out;
+}
+
+// largest |error| over the faces at least `k` faces from each wall (the wall
+// face itself carries no mass flux and is left out of every measure)
+double interior_max(torch::Tensor e, int k) {
+  int nf = e.size(0);
+  return e.narrow(0, k, nf - 2 * k).abs().max().item<double>();
+}
+
+}  // namespace
+
+TEST(WbRefWall, order_table) {
+  std::vector<double> betas = {0.5, 0.};
+  if (char const* e = std::getenv("WB_REF_WALL_BETAS")) {  // scan aid
+    betas.clear();
+    for (std::string tok, s = e; !s.empty();) {
+      auto k = s.find(',');
+      tok = s.substr(0, k);
+      betas.push_back(std::stod(tok));
+      s = k == std::string::npos ? "" : s.substr(k + 1);
+    }
+  }
+  for (double beta : betas) {
+    Profile prof{beta};
+    std::printf("beta %g (depth %.6f, 1 pressure scale height)\n", beta,
+                prof.depth());
+    std::printf(
+        "  nz   face1 dsf   face2 dsf   face1 rhoL  face2 rhoL  face1 rhoR  "
+        "face2 rhoR | top1 dsf    top2 dsf   | interior dsf (>=3 from wall)\n");
+    for (int nz : {16, 32, 64, 128}) {
+      auto e = face_errors(nz, prof);
+      int nf = e.dsf.size(0);
+      auto v = [&](torch::Tensor t, int f) { return t[f].item<double>(); };
+      std::printf(
+          "  %4d %+.3e %+.3e %+.3e %+.3e %+.3e %+.3e | %+.3e %+.3e | "
+          "%.3e\n",
+          nz, v(e.dsf, 1), v(e.dsf, 2), v(e.rl, 1), v(e.rl, 2), v(e.rr, 1),
+          v(e.rr, 2), v(e.dsf, nf - 2), v(e.dsf, nf - 3),
+          interior_max(e.dsf, 3));
+    }
+  }
+}
+
+// The faces next to each wall (one and two cells in) keep the interior's
+// second order: the observed order nz 32 -> 64 is at least 1.7 for the face
+// density reference and for the face densities the solver builds from it, and
+// at nz 64 the reference there is no worse than 1.5 times the largest interior
+// error. With the wall cell repeated past the wall (the clamp) the first face
+// is first order, 1.39e-3 against an interior 1.45e-4 at nz 64.
+void faces_next_to_the_walls_are_second_order(torch::Device device) {
+  Profile prof{0.5};
+  auto c = face_errors(32, prof, device), f = face_errors(64, prof, device);
+  int nc = c.dsf.size(0), nf = f.dsf.size(0);
+  double interior = interior_max(f.dsf, 3);
+  struct Face {
+    char const* name;
+    int ic, iff;
+  };
+  for (auto face :
+       {Face{"bottom 1", 1, 1}, Face{"bottom 2", 2, 2},
+        Face{"top 1", nc - 2, nf - 2}, Face{"top 2", nc - 3, nf - 3}}) {
+    for (auto [what, ec, ef] :
+         {std::tuple{"dsf", c.dsf, f.dsf}, std::tuple{"rho_L", c.rl, f.rl},
+          std::tuple{"rho_R", c.rr, f.rr}}) {
+      double a = std::abs(ec[face.ic].item<double>());
+      double b = std::abs(ef[face.iff].item<double>());
+      double order = std::log2(a / b);
+      std::printf("%-8s %-5s nz 32 %.3e  nz 64 %.3e  order %.2f\n", face.name,
+                  what, a, b, order);
+      EXPECT_GE(order, 1.7) << face.name << " " << what;
+      if (std::string(what) == "dsf") {
+        EXPECT_LE(b, 1.5 * interior)
+            << face.name << " dsf " << b << " vs interior " << interior;
+      }
+    }
+  }
+}
+
+TEST(WbRefWall, faces_next_to_the_walls_are_second_order) {
+  faces_next_to_the_walls_are_second_order(torch::kCPU);
+}
+
+TEST(WbRefWall, faces_next_to_the_walls_are_second_order_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  faces_next_to_the_walls_are_second_order(torch::Device(torch::kCUDA, 0));
+}
+
+int main(int argc, char** argv) {
+  testing::InitGoogleTest(&argc, argv);
+  return RUN_ALL_TESTS();
+}
--
2.43.0

```

## 0002-Default-x1-reference-continue-ln-rho-p-not-rho-p-pas.patch

```diff
From 0e82f76eac4964b522e68856e9c45f683bd145cb Mon Sep 17 00:00:00 2001
From: Zoey Hu <hzin@umich.edu>
Date: Fri, 9 Oct 2026 20:55:18 -0400
Subject: [PATCH 2/3] Default x1 reference: continue ln(rho/p), not rho/p, past
 a clamped wall

024d537 continued r = rho/p linearly past a clamped physical wall,
r_{-k} = r_0 + k (r_0 - r_1). That restores second order at the wall
faces but is unbounded below: r_{-3} -> 0 as (r_1 - r_0)/r_0 -> 1/3.
test_straka_redo (CFL 1.6, nx1 64) then failed in 10/10 perturbed runs
(dT = -15 (1 + k 1e-12)), all at t = 31.67 s with p < 0 in the second
cell below the top wall.

Continue ln r linearly instead, r_{-k} = r_0 (r_0/r_1)^k, falling back
to r_0 when r_0/r_1 is not positive. It equals the linear form to
first order, so the wall order is unchanged:
- test_wb_ref_wall, beta 0.5, face-1 dsf 8.04e-4 / 1.95e-4 / 4.82e-5
  / 1.22e-5 at nz 16-128; orders 1.93-2.06 at faces 1-2 of both walls
  (0.74-1.31 at 37dce4e);
- every interior face and cell is bitwise as at 37dce4e (nz 16-128,
  beta 0.5 and 0); isothermal columns are unchanged.
straka CFL 1.6 ensemble: 9/10 runs reach 60 s (clamp only 10/10,
SNAP_WB_REF4 on 8/10); nx1 32 / 64 / 128 all reach 60 s.
---
 docs/derivations/wb-ref-wall.md  | 78 ++++++++++++++++++++---------
 docs/derivations/wb-ref-wall.tex | 84 +++++++++++++++++++++++---------
 src/hydro/hydro_dispatch.cpp     | 14 +++---
 src/hydro/hydro_ref_x1_impl.h    | 25 +++++-----
 4 files changed, 134 insertions(+), 67 deletions(-)

diff --git a/docs/derivations/wb-ref-wall.md b/docs/derivations/wb-ref-wall.md
index 452b77f..02a75c2 100644
--- a/docs/derivations/wb-ref-wall.md
+++ b/docs/derivations/wb-ref-wall.md
@@ -2,7 +2,7 @@

 This is the default reference, with `SNAP_WB_REF4` off and `dynamics/wb-wall-clamp` on (the default). With the
 repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
-wall, against $O(\Delta z^2)$ elsewhere. A linear continuation of $\rho/p$ past the wall restores the interior
+wall, against $O(\Delta z^2)$ elsewhere. Continuing $\ln(\rho/p)$ linearly past the wall restores the interior
 order there and leaves every other face bit for bit. The code is `src/hydro/hydro_ref_x1_impl.h`
 (`hydro_ref_x1_rop_smooth`, `hydro_ref_x1_cell_impl`), with the tensor (MPS) path in
 `src/hydro/hydro_dispatch.cpp`. The test is `tests/test_wb_ref_wall.cpp`.
@@ -68,52 +68,84 @@ faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times1
 The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
 only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.

-## 4. The closure: continue $\rho/p$ linearly past the wall
+## 4. The closure: continue $\ln(\rho/p)$ linearly past the wall

 Past a clamped wall, take

 $$
-r_{-k} = r_0 + k\,(r_0 - r_1),\qquad k = 1, 2, 3
+r_{-k} = r_0\,(r_0/r_1)^k,\qquad k = 1, 2, 3
 $$

-(and the mirror image at the top), in place of $r_0$. $B$ reproduces a linear profile exactly, so the $O(a)$
-terms above cancel. What remains is the continuation's own curvature error, $\tfrac{k(k+1)}{2}r''\Delta z^2$, which is
-$O(\Delta z^2)$. The wall cells, and faces 0–2, then have the interior's order. For constant $r$ the continuation
-equals $r_0$ exactly, so an isothermal column is unchanged bit for bit.
+(and the mirror image at the top), in place of $r_0$. This is the linear continuation of $\ln r$. It differs from
+the linear continuation of $r$ by $O(\Delta z^2)$, and $B$ reproduces a linear profile exactly, so the $O(a)$ terms
+above cancel. What remains is the
+continuation's own curvature error, $\tfrac{k(k+1)}{2}(\ln r)''\,r\,\Delta z^2$, which is $O(\Delta z^2)$. The wall
+cells, and faces 0–2, then have the interior's order. For constant $r$, $r_0/r_1 = 1$ and $1^k = 1$ exactly, so an
+isothermal column is unchanged bit for bit.

 Guards (the clamp stays):
 - the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
   `test_hydro_ref_x1` hold;
-- a continuation that is not positive falls back to $r_0$.
+- if $r_0/r_1$ is not positive, $r_0$ is used.

 Measured with `test_wb_ref_wall`, $\beta = 0.5$, dsf at face 1:

-| nz | before | after |
-|---|---|---|
-| 16 | $6.16\times10^{-3}$ | $6.48\times10^{-4}$ |
-| 32 | $2.88\times10^{-3}$ | $1.57\times10^{-4}$ |
-| 64 | $1.39\times10^{-3}$ | $3.87\times10^{-5}$ |
-| 128 | $6.84\times10^{-4}$ | $9.78\times10^{-6}$ |
+| nz | clamp only | linear in $r$ (024d537) | linear in $\ln r$ |
+|---|---|---|---|
+| 16 | $6.16\times10^{-3}$ | $6.48\times10^{-4}$ | $8.04\times10^{-4}$ |
+| 32 | $2.88\times10^{-3}$ | $1.57\times10^{-4}$ | $1.95\times10^{-4}$ |
+| 64 | $1.39\times10^{-3}$ | $3.87\times10^{-5}$ | $4.82\times10^{-5}$ |
+| 128 | $6.84\times10^{-4}$ | $9.78\times10^{-6}$ | $1.22\times10^{-5}$ |

-The observed order goes from about 1.05 to about 2.0. The solver's $\rho_L$ at face 1 goes from
-$-2.54\times10^{-4}$ (nz 64) to $8.6\times10^{-6}$. Faces 1–2 at both walls now stay at or below the largest
-interior error ($1.45\times10^{-4}$ at nz 64).
+The observed order goes from about 1.05 to about 2.0 (1.93–2.06 over faces 1–2 at both walls, for dsf,
+$\rho_L$ and $\rho_R$, nz 32 → 64). The solver's $\rho_L$ at face 1 goes from $-2.54\times10^{-4}$ (nz 64) to
+$7.5\times10^{-6}$. Faces 1–2 at both walls stay at or below the largest interior error ($1.45\times10^{-4}$ at
+nz 64; top face 2 is $1.447\times10^{-4}$).

 **What changes.** At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
 plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
 (compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
 `wb-ref4.md`), so `balance_column` and the discrete rest state are unchanged.

-**Why linear, and why not the `SNAP_WB_REF4` closure.**
-- The default reference is second order, so a two-point continuation is enough.
-- It needs only two owned cells and amplifies cell-to-cell noise the least. Its largest weight is $1+k$, against
-  10–20 for a cubic.
+**Why $\ln r$ and not $r$.**
+- The default reference is second order, so a two-point continuation is enough, and both forms give it.
+- A linear continuation in $r$ is not bounded below. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$, which
+  approaches zero as $d \to 1/3$ and goes negative past it. The geometric form stays positive for any positive
+  $r_0, r_1$, and to first order in $d$ it is the same as the linear one.
+- In the over-CFL straka run of `test_straka_redo` (CFL 1.6, nx1 64), the linear form fails robustly and the
+  geometric one does not (§5).
+
+**Why not the `SNAP_WB_REF4` closure.**
 - `SNAP_WB_REF4`'s wall closure (`wb_ref4.cpp`) is a post-pass that replaces $\rho_{\rm ref}$ with
   $p_{\rm ref}F(r)$ and $\rho_{\rm sf}$ with a fourth-order face value on *every* face, so applying it would change
   every interior face. Its cubic continuation is tied to $F$: $F$ with the cubic values returns $r$ at the end
   cells exactly. It also needs four owned cells.
-- A cubic (or quadratic) continuation inside $B$ would also restore second order. It was not chosen for the
-  reasons above.
+- A cubic (or quadratic) continuation inside $B$ would also restore second order, with weights of 10–20 against
+  $1+k$; it was not chosen.
+
+## 5. The straka CFL 1.6 run
+
+`test_straka_redo` runs `examples/straka_single.yaml` with CFL 1.6 and tlim 60 s, and fails if one step needs more
+than 5 redos. CFL 1.6 is past the scheme's stability limit, so this is a robustness test, and it is marginal: most
+redos are triggered by non-finite states. Ensemble of ten runs with $\Delta T = -15(1 + k\cdot10^{-12})$,
+$k = 0..9$, nx1 64, one thread:
+
+| reference | runs reaching 60 s | failures |
+|---|---|---|
+| clamp only | 10/10 | — |
+| clamp only, `SNAP_WB_REF4` on | 8/10 | 25.00 s, 52.60 s |
+| linear in $r$ | 0/10 | all at 31.67 s, cycle 145 |
+| linear in $r$, `SNAP_WB_REF4` on | 9/10 | 48.81 s |
+| linear in $\ln r$ | 9/10 | 48.64 s |
+
+Resolution scan with the unperturbed deck (nx2 = 4 nx1): the clamp-only reference fails at nx1 128 (34.38 s, in
+the interior), the linear one at nx1 64; the geometric one reaches 60 s at nx1 32, 64 and 128, with at most 3
+consecutive redos.
+
+The references at $t = 0$ are not odd for either closure: in the straka column the top cell's $\rho_{\rm ref}$ is
+within 0.002% of the cell average with the linear closure (0.15% with the clamp), and the positivity fallback does
+not fire. The failure of the linear form develops after about 28 s, when the top cells see $|r_1 - r_0|/r_0$ up to
+0.38. That this drives $r_{-k}$ towards zero and starves the top cells is a hypothesis; it was not isolated.

 **Not covered.** Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
 is changed to the same rule but was not run here, since there is no MPS device.
diff --git a/docs/derivations/wb-ref-wall.tex b/docs/derivations/wb-ref-wall.tex
index d342c8e..a7f25bb 100644
--- a/docs/derivations/wb-ref-wall.tex
+++ b/docs/derivations/wb-ref-wall.tex
@@ -18,7 +18,7 @@

 This is the default reference, with \texttt{SNAP\_WB\_REF4} off and \texttt{dynamics/wb-wall-clamp} on (the default). With the
 repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
-wall, against $O(\Delta z^2)$ elsewhere. A linear continuation of $\rho/p$ past the wall restores the interior
+wall, against $O(\Delta z^2)$ elsewhere. Continuing $\ln(\rho/p)$ linearly past the wall restores the interior
 order there and leaves every other face bit for bit. The code is \texttt{src/hydro/hydro\_ref\_x1\_impl.h}
 (\texttt{hydro\_ref\_x1\_rop\_smooth}, \texttt{hydro\_ref\_x1\_cell\_impl}), with the tensor (MPS) path in
 \texttt{src/hydro/hydro\_dispatch.cpp}. The test is \texttt{tests/test\_wb\_ref\_wall.cpp}.
@@ -92,61 +92,99 @@ faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times1
 The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
 only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.

-\section*{4. The closure: continue $\rho/p$ linearly past the wall}
+\section*{4. The closure: continue $\ln(\rho/p)$ linearly past the wall}

 Past a clamped wall, take

 \begin{equation*}
-r_{-k} = r_0 + k\,(r_0 - r_1),\qquad k = 1, 2, 3
+r_{-k} = r_0\,(r_0/r_1)^k,\qquad k = 1, 2, 3
 \end{equation*}

-(and the mirror image at the top), in place of $r_0$. $B$ reproduces a linear profile exactly, so the $O(a)$
-terms above cancel. What remains is the continuation's own curvature error, $\tfrac{k(k+1)}{2}r''\Delta z^2$, which is
-$O(\Delta z^2)$. The wall cells, and faces 0–2, then have the interior's order. For constant $r$ the continuation
-equals $r_0$ exactly, so an isothermal column is unchanged bit for bit.
+(and the mirror image at the top), in place of $r_0$. This is the linear continuation of $\ln r$. It differs from
+the linear continuation of $r$ by $O(\Delta z^2)$, and $B$ reproduces a linear profile exactly, so the $O(a)$ terms
+above cancel. What remains is the
+continuation's own curvature error, $\tfrac{k(k+1)}{2}(\ln r)''\,r\,\Delta z^2$, which is $O(\Delta z^2)$. The wall
+cells, and faces 0–2, then have the interior's order. For constant $r$, $r_0/r_1 = 1$ and $1^k = 1$ exactly, so an
+isothermal column is unchanged bit for bit.

 Guards (the clamp stays):
 \begin{itemize}
 \item the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
   \texttt{test\_hydro\_ref\_x1} hold;
-\item a continuation that is not positive falls back to $r_0$.
+\item if $r_0/r_1$ is not positive, $r_0$ is used.
 \end{itemize}

 Measured with \texttt{test\_wb\_ref\_wall}, $\beta = 0.5$, dsf at face 1:

-\begin{longtable}{lll}
+\begin{longtable}{llll}
 \toprule
-nz & before & after \\
+nz & clamp only & linear in $r$ (024d537) & linear in $\ln r$ \\
 \midrule
-16 & $6.16\times10^{-3}$ & $6.48\times10^{-4}$ \\
-32 & $2.88\times10^{-3}$ & $1.57\times10^{-4}$ \\
-64 & $1.39\times10^{-3}$ & $3.87\times10^{-5}$ \\
-128 & $6.84\times10^{-4}$ & $9.78\times10^{-6}$ \\
+16 & $6.16\times10^{-3}$ & $6.48\times10^{-4}$ & $8.04\times10^{-4}$ \\
+32 & $2.88\times10^{-3}$ & $1.57\times10^{-4}$ & $1.95\times10^{-4}$ \\
+64 & $1.39\times10^{-3}$ & $3.87\times10^{-5}$ & $4.82\times10^{-5}$ \\
+128 & $6.84\times10^{-4}$ & $9.78\times10^{-6}$ & $1.22\times10^{-5}$ \\
 \bottomrule
 \end{longtable}

-The observed order goes from about 1.05 to about 2.0. The solver's $\rho_L$ at face 1 goes from
-$-2.54\times10^{-4}$ (nz 64) to $8.6\times10^{-6}$. Faces 1–2 at both walls now stay at or below the largest
-interior error ($1.45\times10^{-4}$ at nz 64).
+The observed order goes from about 1.05 to about 2.0 (1.93–2.06 over faces 1–2 at both walls, for dsf,
+$\rho_L$ and $\rho_R$, nz 32 → 64). The solver's $\rho_L$ at face 1 goes from $-2.54\times10^{-4}$ (nz 64) to
+$7.5\times10^{-6}$. Faces 1–2 at both walls stay at or below the largest interior error ($1.45\times10^{-4}$ at
+nz 64; top face 2 is $1.447\times10^{-4}$).

 \textbf{What changes.} At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
 plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
 (compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
 \texttt{wb-ref4.md}), so \texttt{balance\_column} and the discrete rest state are unchanged.

-\textbf{Why linear, and why not the \texttt{SNAP\_WB\_REF4} closure.}
+\textbf{Why $\ln r$ and not $r$.}
+\begin{itemize}
+\item The default reference is second order, so a two-point continuation is enough, and both forms give it.
+\item A linear continuation in $r$ is not bounded below. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$, which
+  approaches zero as $d \to 1/3$ and goes negative past it. The geometric form stays positive for any positive
+  $r_0, r_1$, and to first order in $d$ it is the same as the linear one.
+\item In the over-CFL straka run of \texttt{test\_straka\_redo} (CFL 1.6, nx1 64), the linear form fails robustly and the
+  geometric one does not (§5).
+\end{itemize}
+
+\textbf{Why not the \texttt{SNAP\_WB\_REF4} closure.}
 \begin{itemize}
-\item The default reference is second order, so a two-point continuation is enough.
-\item It needs only two owned cells and amplifies cell-to-cell noise the least. Its largest weight is $1+k$, against
-  10–20 for a cubic.
 \item \texttt{SNAP\_WB\_REF4}'s wall closure (\texttt{wb\_ref4.cpp}) is a post-pass that replaces $\rho_{\rm ref}$ with
   $p_{\rm ref}F(r)$ and $\rho_{\rm sf}$ with a fourth-order face value on *every* face, so applying it would change
   every interior face. Its cubic continuation is tied to $F$: $F$ with the cubic values returns $r$ at the end
   cells exactly. It also needs four owned cells.
-\item A cubic (or quadratic) continuation inside $B$ would also restore second order. It was not chosen for the
-  reasons above.
+\item A cubic (or quadratic) continuation inside $B$ would also restore second order, with weights of 10–20 against
+  $1+k$; it was not chosen.
 \end{itemize}

+\section*{5. The straka CFL 1.6 run}
+
+\texttt{test\_straka\_redo} runs \texttt{examples/straka\_single.yaml} with CFL 1.6 and tlim 60 s, and fails if one step needs more
+than 5 redos. CFL 1.6 is past the scheme's stability limit, so this is a robustness test, and it is marginal: most
+redos are triggered by non-finite states. Ensemble of ten runs with $\Delta T = -15(1 + k\cdot10^{-12})$,
+$k = 0..9$, nx1 64, one thread:
+
+\begin{longtable}{lll}
+\toprule
+reference & runs reaching 60 s & failures \\
+\midrule
+clamp only & 10/10 & — \\
+clamp only, \texttt{SNAP\_WB\_REF4} on & 8/10 & 25.00 s, 52.60 s \\
+linear in $r$ & 0/10 & all at 31.67 s, cycle 145 \\
+linear in $r$, \texttt{SNAP\_WB\_REF4} on & 9/10 & 48.81 s \\
+linear in $\ln r$ & 9/10 & 48.64 s \\
+\bottomrule
+\end{longtable}
+
+Resolution scan with the unperturbed deck (nx2 = 4 nx1): the clamp-only reference fails at nx1 128 (34.38 s, in
+the interior), the linear one at nx1 64; the geometric one reaches 60 s at nx1 32, 64 and 128, with at most 3
+consecutive redos.
+
+The references at $t = 0$ are not odd for either closure: in the straka column the top cell's $\rho_{\rm ref}$ is
+within 0.002\% of the cell average with the linear closure (0.15\% with the clamp), and the positivity fallback does
+not fire. The failure of the linear form develops after about 28 s, when the top cells see $|r_1 - r_0|/r_0$ up to
+0.38. That this drives $r_{-k}$ towards zero and starves the top cells is a hypothesis; it was not isolated.
+
 \textbf{Not covered.} Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
 is changed to the same rule but was not run here, since there is no MPS device.

diff --git a/src/hydro/hydro_dispatch.cpp b/src/hydro/hydro_dispatch.cpp
index f6ed166..7d6cada 100644
--- a/src/hydro/hydro_dispatch.cpp
+++ b/src/hydro/hydro_dispatch.cpp
@@ -160,16 +160,16 @@ void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
   auto lo_edge = rop.narrow(-1, 0, 1);
   auto hi_edge = rop.narrow(-1, nc1 - 1, 1);
   auto pad = torch::cat({lo_edge, lo_edge, rop, hi_edge, hi_edge}, -1);
-  // past a clamped wall: rho/p continued linearly from the two cells next to
-  // it where positive, else the wall cell (hydro_ref_x1_rop_smooth); pad
-  // index p holds cell p - 2
+  // past a clamped wall: ln(rho/p) continued linearly from the two cells next
+  // to it, r0 (r0 / r1)^k, where that ratio is positive, else the wall cell
+  // (hydro_ref_x1_rop_smooth); pad index p holds cell p - 2
   if (wall_clamp && phys_in) {
     auto r0 = rop.narrow(-1, il, 1);
     for (int j = -2; j < il; ++j) {
       auto v = r0;
       if (il + 1 <= iu) {
-        auto e = r0 + double(il - j) * (r0 - rop.narrow(-1, il + 1, 1));
-        v = torch::where(e > 0., e, r0);
+        auto q = r0 / rop.narrow(-1, il + 1, 1);
+        v = torch::where(q > 0., r0 * q.pow(double(il - j)), r0);
       }
       pad.narrow(-1, j + 2, 1).copy_(v);
     }
@@ -179,8 +179,8 @@ void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
     for (int j = iu + 1; j < nc1 + 2; ++j) {
       auto v = r0;
       if (iu - 1 >= il) {
-        auto e = r0 + double(j - iu) * (r0 - rop.narrow(-1, iu - 1, 1));
-        v = torch::where(e > 0., e, r0);
+        auto q = r0 / rop.narrow(-1, iu - 1, 1);
+        v = torch::where(q > 0., r0 * q.pow(double(j - iu)), r0);
       }
       pad.narrow(-1, j + 2, 1).copy_(v);
     }
diff --git a/src/hydro/hydro_ref_x1_impl.h b/src/hydro/hydro_ref_x1_impl.h
index e2f51ec..6a2300e 100644
--- a/src/hydro/hydro_ref_x1_impl.h
+++ b/src/hydro/hydro_ref_x1_impl.h
@@ -65,12 +65,13 @@ inline DISPATCH_MACRO void hydro_ref_x1_scan_impl(T const* w, T const* dx1f,
 //! anomalies bypass the high-order reconstruction; a bottom-anchored
 //! isentrope reference errs by orders of magnitude on a stratified column.
 //! Past a clamped wall (ext_lo/ext_hi: the wall side owns at least two cells)
-//! the stencil continues rho/p linearly from the two cells next to the wall
-//! instead of repeating the wall cell. The binomial reproduces a linear profile
-//! exactly, so the wall cells keep the interior's O(dz^2) bias; a repeated wall
-//! cell is exact only for constant rho/p and leaves an O(dz) error at the
-//! first faces (docs/derivations/wb-ref-wall.md). A continuation that is not
-//! positive falls back to the wall cell. Only owned cells are read.
+//! the stencil continues ln(rho/p) linearly from the two cells next to the
+//! wall, r_{-k} = r_0 (r_0 / r_1)^k, instead of repeating the wall cell. That
+//! is linear in index to O(dz^2), so the wall cells keep the interior's
+//! O(dz^2) bias; a repeated wall cell is exact only for constant rho/p and
+//! leaves an O(dz) error at the first faces (docs/derivations/wb-ref-wall.md).
+//! The continuation stays positive; a non-positive ratio keeps the wall cell.
+//! Only owned cells are read.
 template <typename T>
 inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
                                                 int flat, int nc1, int i,
@@ -84,16 +85,12 @@ inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
     int j = i + m;
     if (j < jlo) {
       v[m + 2] = rop(jlo);
-      if (ext_lo) {
-        T e = v[m + 2] + T(jlo - j) * (v[m + 2] - rop(jlo + 1));
-        if (e > T(0)) v[m + 2] = e;
-      }
+      T q = ext_lo ? v[m + 2] / rop(jlo + 1) : T(0);
+      if (q > T(0)) v[m + 2] *= pow(q, T(jlo - j));
     } else if (j > jhi) {
       v[m + 2] = rop(jhi);
-      if (ext_hi) {
-        T e = v[m + 2] + T(j - jhi) * (v[m + 2] - rop(jhi - 1));
-        if (e > T(0)) v[m + 2] = e;
-      }
+      T q = ext_hi ? v[m + 2] / rop(jhi - 1) : T(0);
+      if (q > T(0)) v[m + 2] *= pow(q, T(j - jhi));
     } else {
       v[m + 2] = rop(j);
     }
--
2.43.0

```

## 0003-Default-x1-reference-wall-continuation-linear-where-.patch

```diff
From ac4dc5686a6a2062dec90285f45130ef29802b41 Mon Sep 17 00:00:00 2001
From: Zoey Hu <hzin@umich.edu>
Date: Fri, 9 Oct 2026 21:11:38 -0400
Subject: [PATCH 3/3] Default x1 reference: wall continuation linear where
 rho/p falls, ln where it rises

0e82f76 continued ln(rho/p) past a clamped wall, r0 (r0/r1)^k. That
is bounded below but not above: next to a nearly empty cell
(test_face_floor's unresolved column, top neighbour dipped to 1e-4)
it gives r0 1e4^k, and the dipped-face mass flux becomes 3.36e-7,
against 2.83e-8 for the linear form and 3.0e-8 for the clamp.

Take, per column, the branch that stays closer to r0
(hydro_ref_x1_wall_rop): linear, r0 + k (r0 - r1), when r1 <= r0, and
ln-linear, r0 (r0/r1)^k, when r1 > r0. For r1 >= 0 the continuation
then lies in [r0 (r0/r1)^k, r0 (1 + k)]: positive and bounded.
- test_wb_ref_wall GREEN: orders 1.81-2.12 at faces 1-2 of both
  walls; face-1 dsf (beta 0.5) 8.04e-4 / 1.95e-4 / 4.82e-5 / 1.22e-5 at
  nz 16-128;
- every interior face and cell is bitwise as at 37dce4e (nz 16-128,
  beta 0.5 and 0); the top wall (linear branch) is bitwise as at
  024d537;
- test_face_floor: 2.8319e-8, as at 024d537.
straka CFL 1.6, nx1 64: the test deck passes. Perturbed runs
dT = -15 (1 + k eps) reaching 60 s:
- eps 1e-12: 10/10, staying on one trajectory;
- eps 1e-4: 18/20 (clamp 20/20, linear 18/20, ln 19/20).
nx1 32 / 64 / 128 all reach 60 s.
---
 docs/derivations/wb-ref-wall.md  | 105 +++++++++++++++++-------------
 docs/derivations/wb-ref-wall.tex | 107 ++++++++++++++++++-------------
 src/hydro/hydro_dispatch.cpp     |  17 +++--
 src/hydro/hydro_ref_x1_impl.h    |  35 ++++++----
 4 files changed, 156 insertions(+), 108 deletions(-)

diff --git a/docs/derivations/wb-ref-wall.md b/docs/derivations/wb-ref-wall.md
index 02a75c2..7db902f 100644
--- a/docs/derivations/wb-ref-wall.md
+++ b/docs/derivations/wb-ref-wall.md
@@ -2,8 +2,8 @@

 This is the default reference, with `SNAP_WB_REF4` off and `dynamics/wb-wall-clamp` on (the default). With the
 repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
-wall, against $O(\Delta z^2)$ elsewhere. Continuing $\ln(\rho/p)$ linearly past the wall restores the interior
-order there and leaves every other face bit for bit. The code is `src/hydro/hydro_ref_x1_impl.h`
+wall, against $O(\Delta z^2)$ elsewhere. Continuing $\rho/p$ past the wall, linearly or ln-linearly, restores the
+interior order there and leaves every other face bit for bit. The code is `src/hydro/hydro_ref_x1_impl.h`
 (`hydro_ref_x1_rop_smooth`, `hydro_ref_x1_cell_impl`), with the tensor (MPS) path in
 `src/hydro/hydro_dispatch.cpp`. The test is `tests/test_wb_ref_wall.cpp`.

@@ -68,53 +68,60 @@ faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times1
 The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
 only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.

-## 4. The closure: continue $\ln(\rho/p)$ linearly past the wall
+## 4. The closure: continue $\rho/p$ past the wall, linearly or ln-linearly

 Past a clamped wall, take

 $$
-r_{-k} = r_0\,(r_0/r_1)^k,\qquad k = 1, 2, 3
+r_{-k} = \begin{cases} r_0 + k\,(r_0 - r_1), & r_1 \le r_0,\\ r_0\,(r_0/r_1)^k, & r_1 > r_0,\end{cases}
+\qquad k = 1, 2, 3
 $$

-(and the mirror image at the top), in place of $r_0$. This is the linear continuation of $\ln r$. It differs from
-the linear continuation of $r$ by $O(\Delta z^2)$, and $B$ reproduces a linear profile exactly, so the $O(a)$ terms
-above cancel. What remains is the
-continuation's own curvature error, $\tfrac{k(k+1)}{2}(\ln r)''\,r\,\Delta z^2$, which is $O(\Delta z^2)$. The wall
-cells, and faces 0–2, then have the interior's order. For constant $r$, $r_0/r_1 = 1$ and $1^k = 1$ exactly, so an
-isothermal column is unchanged bit for bit.
+(and the mirror image at the top), in place of $r_0$ (`hydro_ref_x1_wall_rop`). The first branch is the linear
+continuation of $r$ and the second that of $\ln r$. The two differ by $O(\Delta z^2)$, and $B$ reproduces a linear
+profile exactly, so the $O(a)$ terms above cancel. What remains is the continuation's own curvature error,
+$\tfrac{k(k+1)}{2}\Delta z^2$ times $r''$ or $(\ln r)''\,r$, which is $O(\Delta z^2)$. The wall cells, and faces
+0–2, then have the interior's order. For constant $r$ the first branch gives $r_0$ exactly, so an isothermal
+column is unchanged bit for bit.
+
+**Why two branches.** Each branch is unbounded on one side:
+- linear in $r$ goes to zero when $r$ rises away from the wall. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$
+  vanishes at $d = 1/3$ and is negative past it;
+- ln-linear goes to infinity when $r$ falls away from the wall. A nearly empty neighbour, $r_1 \ll r_0$, gives
+  $r_0(r_0/r_1)^k$.
+
+Each case takes the branch that stays closer to $r_0$, so for $r_1 \ge 0$ the continuation lies in
+$[\,r_0(r_0/r_1)^k,\; r_0(1+k)\,]$. In `test_face_floor`'s unresolved column, the cell next to the top wall is
+dipped to $10^{-4}$, and the dipped-face mass flux is
+- $3.0\times10^{-8}$ with the clamp,
+- $2.83\times10^{-8}$ with either the linear form or this closure,
+- $3.36\times10^{-7}$ with the ln-linear form everywhere.

 Guards (the clamp stays):
 - the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
   `test_hydro_ref_x1` hold;
-- if $r_0/r_1$ is not positive, $r_0$ is used.
+- a value that is not positive falls back to $r_0$.

-Measured with `test_wb_ref_wall`, $\beta = 0.5$, dsf at face 1:
+Measured with `test_wb_ref_wall`, $\beta = 0.5$, dsf at face 1 (the bottom wall, where $r$ rises away from the
+wall, so the ln-linear branch applies; the top wall takes the linear branch):

-| nz | clamp only | linear in $r$ (024d537) | linear in $\ln r$ |
+| nz | clamp only | linear in $r$ everywhere | this closure |
 |---|---|---|---|
 | 16 | $6.16\times10^{-3}$ | $6.48\times10^{-4}$ | $8.04\times10^{-4}$ |
 | 32 | $2.88\times10^{-3}$ | $1.57\times10^{-4}$ | $1.95\times10^{-4}$ |
 | 64 | $1.39\times10^{-3}$ | $3.87\times10^{-5}$ | $4.82\times10^{-5}$ |
 | 128 | $6.84\times10^{-4}$ | $9.78\times10^{-6}$ | $1.22\times10^{-5}$ |

-The observed order goes from about 1.05 to about 2.0 (1.93–2.06 over faces 1–2 at both walls, for dsf,
+The observed order goes from about 1.05 to about 2.0 (1.81–2.12 over faces 1–2 at both walls, for dsf,
 $\rho_L$ and $\rho_R$, nz 32 → 64). The solver's $\rho_L$ at face 1 goes from $-2.54\times10^{-4}$ (nz 64) to
 $7.5\times10^{-6}$. Faces 1–2 at both walls stay at or below the largest interior error ($1.45\times10^{-4}$ at
-nz 64; top face 2 is $1.447\times10^{-4}$).
+nz 64).

 **What changes.** At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
 plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
 (compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
 `wb-ref4.md`), so `balance_column` and the discrete rest state are unchanged.

-**Why $\ln r$ and not $r$.**
-- The default reference is second order, so a two-point continuation is enough, and both forms give it.
-- A linear continuation in $r$ is not bounded below. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$, which
-  approaches zero as $d \to 1/3$ and goes negative past it. The geometric form stays positive for any positive
-  $r_0, r_1$, and to first order in $d$ it is the same as the linear one.
-- In the over-CFL straka run of `test_straka_redo` (CFL 1.6, nx1 64), the linear form fails robustly and the
-  geometric one does not (§5).
-
 **Why not the `SNAP_WB_REF4` closure.**
 - `SNAP_WB_REF4`'s wall closure (`wb_ref4.cpp`) is a post-pass that replaces $\rho_{\rm ref}$ with
   $p_{\rm ref}F(r)$ and $\rho_{\rm sf}$ with a fourth-order face value on *every* face, so applying it would change
@@ -127,25 +134,33 @@ plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell

 `test_straka_redo` runs `examples/straka_single.yaml` with CFL 1.6 and tlim 60 s, and fails if one step needs more
 than 5 redos. CFL 1.6 is past the scheme's stability limit, so this is a robustness test, and it is marginal: most
-redos are triggered by non-finite states. Ensemble of ten runs with $\Delta T = -15(1 + k\cdot10^{-12})$,
-$k = 0..9$, nx1 64, one thread:
-
-| reference | runs reaching 60 s | failures |
-|---|---|---|
-| clamp only | 10/10 | — |
-| clamp only, `SNAP_WB_REF4` on | 8/10 | 25.00 s, 52.60 s |
-| linear in $r$ | 0/10 | all at 31.67 s, cycle 145 |
-| linear in $r$, `SNAP_WB_REF4` on | 9/10 | 48.81 s |
-| linear in $\ln r$ | 9/10 | 48.64 s |
-
-Resolution scan with the unperturbed deck (nx2 = 4 nx1): the clamp-only reference fails at nx1 128 (34.38 s, in
-the interior), the linear one at nx1 64; the geometric one reaches 60 s at nx1 32, 64 and 128, with at most 3
-consecutive redos.
-
-The references at $t = 0$ are not odd for either closure: in the straka column the top cell's $\rho_{\rm ref}$ is
-within 0.002% of the cell average with the linear closure (0.15% with the clamp), and the positivity fallback does
-not fire. The failure of the linear form develops after about 28 s, when the top cells see $|r_1 - r_0|/r_0$ up to
-0.38. That this drives $r_{-k}$ towards zero and starves the top cells is a hypothesis; it was not isolated.
-
-**Not covered.** Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
-is changed to the same rule but was not run here, since there is no MPS device.
+redos are triggered by non-finite states. Runs reaching 60 s, with nx1 64, one thread, and
+$\Delta T = -15(1 + k\epsilon)$:
+
+| reference | test deck | $\epsilon = 10^{-12}$, $k = 0..9$ | $\epsilon = 10^{-4}$, $k = 0..19$ |
+|---|---|---|---|
+| clamp only | pass | 10/10 | 20/20 |
+| linear in $r$ everywhere | fail (31.67 s) | 0/10 | 18/20 |
+| ln-linear everywhere | pass | 9/10 | 19/20 |
+| this closure | pass | 10/10 | 18/20 |
+
+With $\epsilon = 10^{-12}$ the runs of this closure stay on one trajectory, ending within $10^{-4}$ in kinetic
+energy, so that column says little beyond the test deck itself. The $\epsilon = 10^{-4}$ column does not separate
+the four references. With `SNAP_WB_REF4` on, the $10^{-12}$ ensemble gives 8/10 on the clamp-only reference and
+9/10 on the linear one.
+
+Resolution scan with the test deck (nx2 = 4 nx1):
+- the clamp-only reference fails at nx1 128 (34.38 s, in the interior);
+- the linear one fails at nx1 64;
+- this closure reaches 60 s at nx1 32, 64 and 128, with at most 3 consecutive redos.
+
+**The linear form's failure.** The references at $t = 0$ are not odd for any closure. In the straka column the top
+cell's $\rho_{\rm ref}$ is within 0.002% of the cell average with the continuation, against 0.15% with the clamp,
+and the positivity fallback does not fire. The failure develops after about 28 s:
+- on the failing run, the linear $r_{+3}/r_0$ at the top wall falls to 0.35 at 30.9 s and to $-0.15$ at 31.67 s;
+- on the clamp-only run, which survives, the same quantity would reach $-4.9$ at 32.1 s.
+
+That the near-zero continuation starves the top cells is a hypothesis; it was not isolated.
+
+**Not covered.** Non-uniform x1: the continuation is in index, as the binomial is. The MPS tensor path is changed
+to the same rule but was not run here, since there is no MPS device.
diff --git a/docs/derivations/wb-ref-wall.tex b/docs/derivations/wb-ref-wall.tex
index a7f25bb..86833d5 100644
--- a/docs/derivations/wb-ref-wall.tex
+++ b/docs/derivations/wb-ref-wall.tex
@@ -18,8 +18,8 @@

 This is the default reference, with \texttt{SNAP\_WB\_REF4} off and \texttt{dynamics/wb-wall-clamp} on (the default). With the
 repeated wall cell, the face density reference has an $O(\Delta z)$ error at the first three faces next to each
-wall, against $O(\Delta z^2)$ elsewhere. Continuing $\ln(\rho/p)$ linearly past the wall restores the interior
-order there and leaves every other face bit for bit. The code is \texttt{src/hydro/hydro\_ref\_x1\_impl.h}
+wall, against $O(\Delta z^2)$ elsewhere. Continuing $\rho/p$ past the wall, linearly or ln-linearly, restores the
+interior order there and leaves every other face bit for bit. The code is \texttt{src/hydro/hydro\_ref\_x1\_impl.h}
 (\texttt{hydro\_ref\_x1\_rop\_smooth}, \texttt{hydro\_ref\_x1\_cell\_impl}), with the tensor (MPS) path in
 \texttt{src/hydro/hydro\_dispatch.cpp}. The test is \texttt{tests/test\_wb\_ref\_wall.cpp}.

@@ -92,33 +92,52 @@ faces 1 and 2 are also first order (measured: $\rho_L$ at face 1 is $-5.2\times1
 The mirror is not the source. Applied to a $\rho'$ that is $O(\Delta z^2)$ and smooth near the wall, it costs
 only $O(\Delta z^2)$. The source is the bias in $\rho_{\rm ref}$.

-\section*{4. The closure: continue $\ln(\rho/p)$ linearly past the wall}
+\section*{4. The closure: continue $\rho/p$ past the wall, linearly or ln-linearly}

 Past a clamped wall, take

 \begin{equation*}
-r_{-k} = r_0\,(r_0/r_1)^k,\qquad k = 1, 2, 3
+r_{-k} = \begin{cases} r_0 + k\,(r_0 - r_1), & r_1 \le r_0,\\ r_0\,(r_0/r_1)^k, & r_1 > r_0,\end{cases}
+\qquad k = 1, 2, 3
 \end{equation*}

-(and the mirror image at the top), in place of $r_0$. This is the linear continuation of $\ln r$. It differs from
-the linear continuation of $r$ by $O(\Delta z^2)$, and $B$ reproduces a linear profile exactly, so the $O(a)$ terms
-above cancel. What remains is the
-continuation's own curvature error, $\tfrac{k(k+1)}{2}(\ln r)''\,r\,\Delta z^2$, which is $O(\Delta z^2)$. The wall
-cells, and faces 0–2, then have the interior's order. For constant $r$, $r_0/r_1 = 1$ and $1^k = 1$ exactly, so an
-isothermal column is unchanged bit for bit.
+(and the mirror image at the top), in place of $r_0$ (\texttt{hydro\_ref\_x1\_wall\_rop}). The first branch is the linear
+continuation of $r$ and the second that of $\ln r$. The two differ by $O(\Delta z^2)$, and $B$ reproduces a linear
+profile exactly, so the $O(a)$ terms above cancel. What remains is the continuation's own curvature error,
+$\tfrac{k(k+1)}{2}\Delta z^2$ times $r''$ or $(\ln r)''\,r$, which is $O(\Delta z^2)$. The wall cells, and faces
+0–2, then have the interior's order. For constant $r$ the first branch gives $r_0$ exactly, so an isothermal
+column is unchanged bit for bit.
+
+\textbf{Why two branches.} Each branch is unbounded on one side:
+\begin{itemize}
+\item linear in $r$ goes to zero when $r$ rises away from the wall. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$
+  vanishes at $d = 1/3$ and is negative past it;
+\item ln-linear goes to infinity when $r$ falls away from the wall. A nearly empty neighbour, $r_1 \ll r_0$, gives
+  $r_0(r_0/r_1)^k$.
+\end{itemize}
+
+Each case takes the branch that stays closer to $r_0$, so for $r_1 \ge 0$ the continuation lies in
+$[\,r_0(r_0/r_1)^k,\; r_0(1+k)\,]$. In \texttt{test\_face\_floor}'s unresolved column, the cell next to the top wall is
+dipped to $10^{-4}$, and the dipped-face mass flux is
+\begin{itemize}
+\item $3.0\times10^{-8}$ with the clamp,
+\item $2.83\times10^{-8}$ with either the linear form or this closure,
+\item $3.36\times10^{-7}$ with the ln-linear form everywhere.
+\end{itemize}

 Guards (the clamp stays):
 \begin{itemize}
 \item the wall side must own at least two cells, so only owned cells are read and the clamp's property tests in
   \texttt{test\_hydro\_ref\_x1} hold;
-\item if $r_0/r_1$ is not positive, $r_0$ is used.
+\item a value that is not positive falls back to $r_0$.
 \end{itemize}

-Measured with \texttt{test\_wb\_ref\_wall}, $\beta = 0.5$, dsf at face 1:
+Measured with \texttt{test\_wb\_ref\_wall}, $\beta = 0.5$, dsf at face 1 (the bottom wall, where $r$ rises away from the
+wall, so the ln-linear branch applies; the top wall takes the linear branch):

 \begin{longtable}{llll}
 \toprule
-nz & clamp only & linear in $r$ (024d537) & linear in $\ln r$ \\
+nz & clamp only & linear in $r$ everywhere & this closure \\
 \midrule
 16 & $6.16\times10^{-3}$ & $6.48\times10^{-4}$ & $8.04\times10^{-4}$ \\
 32 & $2.88\times10^{-3}$ & $1.57\times10^{-4}$ & $1.95\times10^{-4}$ \\
@@ -127,26 +146,16 @@ nz & clamp only & linear in $r$ (024d537) & linear in $\ln r$ \\
 \bottomrule
 \end{longtable}

-The observed order goes from about 1.05 to about 2.0 (1.93–2.06 over faces 1–2 at both walls, for dsf,
+The observed order goes from about 1.05 to about 2.0 (1.81–2.12 over faces 1–2 at both walls, for dsf,
 $\rho_L$ and $\rho_R$, nz 32 → 64). The solver's $\rho_L$ at face 1 goes from $-2.54\times10^{-4}$ (nz 64) to
 $7.5\times10^{-6}$. Faces 1–2 at both walls stay at or below the largest interior error ($1.45\times10^{-4}$ at
-nz 64; top face 2 is $1.447\times10^{-4}$).
+nz 64).

 \textbf{What changes.} At each clamped physical wall: $\rho_{\rm sf}$ at faces 0, 1, 2 and $\rho_{\rm ref}$ at cells 0, 1,
 plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell are bit for bit as before
 (compared at nz 16–128). The rest balance does not involve $\rho_{\rm sf}$ or $\rho_{\rm ref}$ (§1 of
 \texttt{wb-ref4.md}), so \texttt{balance\_column} and the discrete rest state are unchanged.

-\textbf{Why $\ln r$ and not $r$.}
-\begin{itemize}
-\item The default reference is second order, so a two-point continuation is enough, and both forms give it.
-\item A linear continuation in $r$ is not bounded below. With $d = (r_1 - r_0)/r_0$, $r_{-3} = r_0(1 - 3d)$, which
-  approaches zero as $d \to 1/3$ and goes negative past it. The geometric form stays positive for any positive
-  $r_0, r_1$, and to first order in $d$ it is the same as the linear one.
-\item In the over-CFL straka run of \texttt{test\_straka\_redo} (CFL 1.6, nx1 64), the linear form fails robustly and the
-  geometric one does not (§5).
-\end{itemize}
-
 \textbf{Why not the \texttt{SNAP\_WB\_REF4} closure.}
 \begin{itemize}
 \item \texttt{SNAP\_WB\_REF4}'s wall closure (\texttt{wb\_ref4.cpp}) is a post-pass that replaces $\rho_{\rm ref}$ with
@@ -161,31 +170,43 @@ plus their ghost rows. $p_{\rm sf}$, $p_{\rm ref}$ and every other face and cell

 \texttt{test\_straka\_redo} runs \texttt{examples/straka\_single.yaml} with CFL 1.6 and tlim 60 s, and fails if one step needs more
 than 5 redos. CFL 1.6 is past the scheme's stability limit, so this is a robustness test, and it is marginal: most
-redos are triggered by non-finite states. Ensemble of ten runs with $\Delta T = -15(1 + k\cdot10^{-12})$,
-$k = 0..9$, nx1 64, one thread:
+redos are triggered by non-finite states. Runs reaching 60 s, with nx1 64, one thread, and
+$\Delta T = -15(1 + k\epsilon)$:

-\begin{longtable}{lll}
+\begin{longtable}{llll}
 \toprule
-reference & runs reaching 60 s & failures \\
+reference & test deck & $\epsilon = 10^{-12}$, $k = 0..9$ & $\epsilon = 10^{-4}$, $k = 0..19$ \\
 \midrule
-clamp only & 10/10 & — \\
-clamp only, \texttt{SNAP\_WB\_REF4} on & 8/10 & 25.00 s, 52.60 s \\
-linear in $r$ & 0/10 & all at 31.67 s, cycle 145 \\
-linear in $r$, \texttt{SNAP\_WB\_REF4} on & 9/10 & 48.81 s \\
-linear in $\ln r$ & 9/10 & 48.64 s \\
+clamp only & pass & 10/10 & 20/20 \\
+linear in $r$ everywhere & fail (31.67 s) & 0/10 & 18/20 \\
+ln-linear everywhere & pass & 9/10 & 19/20 \\
+this closure & pass & 10/10 & 18/20 \\
 \bottomrule
 \end{longtable}

-Resolution scan with the unperturbed deck (nx2 = 4 nx1): the clamp-only reference fails at nx1 128 (34.38 s, in
-the interior), the linear one at nx1 64; the geometric one reaches 60 s at nx1 32, 64 and 128, with at most 3
-consecutive redos.
+With $\epsilon = 10^{-12}$ the runs of this closure stay on one trajectory, ending within $10^{-4}$ in kinetic
+energy, so that column says little beyond the test deck itself. The $\epsilon = 10^{-4}$ column does not separate
+the four references. With \texttt{SNAP\_WB\_REF4} on, the $10^{-12}$ ensemble gives 8/10 on the clamp-only reference and
+9/10 on the linear one.
+
+Resolution scan with the test deck (nx2 = 4 nx1):
+\begin{itemize}
+\item the clamp-only reference fails at nx1 128 (34.38 s, in the interior);
+\item the linear one fails at nx1 64;
+\item this closure reaches 60 s at nx1 32, 64 and 128, with at most 3 consecutive redos.
+\end{itemize}
+
+\textbf{The linear form's failure.} The references at $t = 0$ are not odd for any closure. In the straka column the top
+cell's $\rho_{\rm ref}$ is within 0.002\% of the cell average with the continuation, against 0.15\% with the clamp,
+and the positivity fallback does not fire. The failure develops after about 28 s:
+\begin{itemize}
+\item on the failing run, the linear $r_{+3}/r_0$ at the top wall falls to 0.35 at 30.9 s and to $-0.15$ at 31.67 s;
+\item on the clamp-only run, which survives, the same quantity would reach $-4.9$ at 32.1 s.
+\end{itemize}

-The references at $t = 0$ are not odd for either closure: in the straka column the top cell's $\rho_{\rm ref}$ is
-within 0.002\% of the cell average with the linear closure (0.15\% with the clamp), and the positivity fallback does
-not fire. The failure of the linear form develops after about 28 s, when the top cells see $|r_1 - r_0|/r_0$ up to
-0.38. That this drives $r_{-k}$ towards zero and starves the top cells is a hypothesis; it was not isolated.
+That the near-zero continuation starves the top cells is a hypothesis; it was not isolated.

-\textbf{Not covered.} Non-uniform x1: the continuation is linear in index, as the binomial is. The MPS tensor path
-is changed to the same rule but was not run here, since there is no MPS device.
+\textbf{Not covered.} Non-uniform x1: the continuation is in index, as the binomial is. The MPS tensor path is changed
+to the same rule but was not run here, since there is no MPS device.

 \end{document}
diff --git a/src/hydro/hydro_dispatch.cpp b/src/hydro/hydro_dispatch.cpp
index 7d6cada..aeab1d0 100644
--- a/src/hydro/hydro_dispatch.cpp
+++ b/src/hydro/hydro_dispatch.cpp
@@ -160,16 +160,20 @@ void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
   auto lo_edge = rop.narrow(-1, 0, 1);
   auto hi_edge = rop.narrow(-1, nc1 - 1, 1);
   auto pad = torch::cat({lo_edge, lo_edge, rop, hi_edge, hi_edge}, -1);
-  // past a clamped wall: ln(rho/p) continued linearly from the two cells next
-  // to it, r0 (r0 / r1)^k, where that ratio is positive, else the wall cell
-  // (hydro_ref_x1_rop_smooth); pad index p holds cell p - 2
+  // past a clamped wall: rho/p continued from the two cells next to it,
+  // linearly where it falls towards the wall and ln-linearly where it rises,
+  // else the wall cell (hydro_ref_x1_wall_rop); pad index p holds cell p - 2
+  auto wall_rop = [](torch::Tensor const& r0, torch::Tensor const& r1, int k) {
+    auto e = torch::where(r1 > r0, r0 * (r0 / r1).pow(double(k)),
+                          r0 + double(k) * (r0 - r1));
+    return torch::where(e > 0., e, r0);
+  };
   if (wall_clamp && phys_in) {
     auto r0 = rop.narrow(-1, il, 1);
     for (int j = -2; j < il; ++j) {
       auto v = r0;
       if (il + 1 <= iu) {
-        auto q = r0 / rop.narrow(-1, il + 1, 1);
-        v = torch::where(q > 0., r0 * q.pow(double(il - j)), r0);
+        v = wall_rop(r0, rop.narrow(-1, il + 1, 1), il - j);
       }
       pad.narrow(-1, j + 2, 1).copy_(v);
     }
@@ -179,8 +183,7 @@ void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
     for (int j = iu + 1; j < nc1 + 2; ++j) {
       auto v = r0;
       if (iu - 1 >= il) {
-        auto q = r0 / rop.narrow(-1, iu - 1, 1);
-        v = torch::where(q > 0., r0 * q.pow(double(j - iu)), r0);
+        v = wall_rop(r0, rop.narrow(-1, iu - 1, 1), j - iu);
       }
       pad.narrow(-1, j + 2, 1).copy_(v);
     }
diff --git a/src/hydro/hydro_ref_x1_impl.h b/src/hydro/hydro_ref_x1_impl.h
index 6a2300e..e38f319 100644
--- a/src/hydro/hydro_ref_x1_impl.h
+++ b/src/hydro/hydro_ref_x1_impl.h
@@ -59,19 +59,30 @@ inline DISPATCH_MACRO void hydro_ref_x1_scan_impl(T const* w, T const* dx1f,
   }
 }

+//! rho/p k cells past a wall, from the wall cell r0 and its neighbour r1:
+//! linear, r0 + k (r0 - r1), where rho/p falls towards the wall (r1 <= r0),
+//! and ln-linear, r0 (r0 / r1)^k, where it rises (r1 > r0). Each is the
+//! branch that stays closer to r0, so the continuation lies within
+//! [r0 (r0 / r1)^k, r0 (1 + k)] for r1 >= 0: positive, and bounded above when
+//! r1 is nearly empty. A non-positive value keeps the wall cell.
+template <typename T>
+inline DISPATCH_MACRO T hydro_ref_x1_wall_rop(T r0, T r1, int k) {
+  T e = r1 > r0 ? r0 * pow(r0 / r1, T(k)) : r0 + T(k) * (r0 - r1);
+  return e > T(0) ? e : r0;
+}
+
 //! rho/p smoothed by a 5-point binomial along x1: the reference must
 //! track the column profile at LARGE scales only. An unsmoothed local rho/p
 //! makes rho' degenerate with the pressure perturbation, so entropy/buoyancy
 //! anomalies bypass the high-order reconstruction; a bottom-anchored
 //! isentrope reference errs by orders of magnitude on a stratified column.
 //! Past a clamped wall (ext_lo/ext_hi: the wall side owns at least two cells)
-//! the stencil continues ln(rho/p) linearly from the two cells next to the
-//! wall, r_{-k} = r_0 (r_0 / r_1)^k, instead of repeating the wall cell. That
-//! is linear in index to O(dz^2), so the wall cells keep the interior's
-//! O(dz^2) bias; a repeated wall cell is exact only for constant rho/p and
-//! leaves an O(dz) error at the first faces (docs/derivations/wb-ref-wall.md).
-//! The continuation stays positive; a non-positive ratio keeps the wall cell.
-//! Only owned cells are read.
+//! the stencil continues rho/p from the two cells next to the wall instead of
+//! repeating the wall cell (hydro_ref_x1_wall_rop). Either continuation is
+//! linear in index to O(dz^2), so the wall cells keep the interior's O(dz^2)
+//! bias; a repeated wall cell is exact only for constant rho/p and leaves an
+//! O(dz) error at the first faces (docs/derivations/wb-ref-wall.md). Only
+//! owned cells are read.
 template <typename T>
 inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
                                                 int flat, int nc1, int i,
@@ -84,13 +95,11 @@ inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
   for (int m = -2; m <= 2; ++m) {
     int j = i + m;
     if (j < jlo) {
-      v[m + 2] = rop(jlo);
-      T q = ext_lo ? v[m + 2] / rop(jlo + 1) : T(0);
-      if (q > T(0)) v[m + 2] *= pow(q, T(jlo - j));
+      v[m + 2] = ext_lo ? hydro_ref_x1_wall_rop(rop(jlo), rop(jlo + 1), jlo - j)
+                        : rop(jlo);
     } else if (j > jhi) {
-      v[m + 2] = rop(jhi);
-      T q = ext_hi ? v[m + 2] / rop(jhi - 1) : T(0);
-      if (q > T(0)) v[m + 2] *= pow(q, T(j - jhi));
+      v[m + 2] = ext_hi ? hydro_ref_x1_wall_rop(rop(jhi), rop(jhi - 1), j - jhi)
+                        : rop(jhi);
     } else {
       v[m + 2] = rop(j);
     }
--
2.43.0

```
