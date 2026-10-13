# v1 small items

Small findings kept out of the chapter text: each is one line of fix for the named owner, with the evidence that
found it. The code pin is snapy@6fbb39750f62b83df096058a4746e77d0a634bc5.

## From the chapter 4 rewrite

| # | where | item | owner | evidence |
|---|---|---|---|---|
| 1 | `book/chapters/15-verification/_ch04-spatial-discretization.qmd` | States the source pin as e894700 and describes `recon_check.py` `[C6]` as "`type: ppm` is donor cell"; at the pin `PPMInterpImpl::forward` throws, and `[C6]` checks only the test template `interp_ppm`. | ch15 | `src/recon/ppm.cpp` at the pin; @sec-ch04-ppm |
| 2 | `book/chapters/16-known-limits.qmd` (ch04 rows) | Line references are at e894700 (`interp_simple.hpp:73-75`, `hydro_forward.cpp:314-344`, `riemann_solver.cpp:39-48`); the cp3 row cites the test-only template, not `Center3InterpImpl`. | ch16 | `tools/code_anchors.py` at the pin |
| 3 | `src/snapy_report/ch04/{recon,operator,solvers,seam,gnomonic,covariance}_check.py` | Headers name e894700. The ported code is unchanged at the pin for the parts they port (the reconstruction and Riemann directories, `d1_centred` and the $x_1$ correction line); `derivation_check.py` `[C6]` ties the ports to the production rows. The headers can be re-pinned without changing any output. | ch04 | `git diff e894700 6fbb397 -- src/recon src/riemann` is empty |
| 4 | `tests/test_flux_covariance_rows.py` (snapy) | The dry Cartesian arm's recorded values hold only with `SNAP_GRAVITY_WORK_RADIAL_EXACT=0`, which the ctest entry sets; run with the switch at its default it gives $+0.0033$ against the recorded $+0.0348$ at $n_z = 16$ and fails. | maintainers | run of the test at the pin with and without the variable |
| 5 | `src/riemann/riemann_solver.cpp` (snapy) | `RiemannSolverOptionsImpl::from_yaml(filename, section)` tests `config[section]` but then reads `config["dynamics"]`; with the only caller passing `"dynamics"` it has no effect. | maintainers | code reading at the pin |
| 6 | `src/riemann/hllc_impl.h`, `src/riemann/plume_roe.cpp` (snapy) | `umid` (HLLC) and the Roe averages, Jacobian entries and polynomial coefficients of plume-roe are computed and never used. | maintainers | code reading at the pin |
| 7 | `src/recon/interpolation.cpp` (snapy) | `type: ppm` is accepted and the first stage throws; refusing it in `InterpImpl::create` would fail at parse time instead. | maintainers | the probe run of @sec-ch04-framework |
| 8 | `src/recon/reconstruct.hpp` (snapy) | `ReconstructOptionsImpl::shock` defaults to true while `from_yaml` writes false when the block exists: a deck without a `reconstruct` block runs with `shock` on. | maintainers | the probe run of @sec-ch04-framework |
| 9 | `tests/CMakeLists.txt` (snapy) | The shallow-water reference decks are registered only with `FULL_TESTS`, so a default build runs no `shallow-roe` test. | maintainers | `ctest -N` of the pin build |
| 10 | `NOTATION.md` §1 | Chapters 3, 4 and 12 name the face moment and the face-centroid shift three ways; ISSUES.md "Chapter 4 local symbols" lists them. | editor | the three sections |
