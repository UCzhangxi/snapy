Status: O4 re-scoring complete from existing D3 outputs: **smooth5, isentrope, none, frozen PASS; local_polytrope FAIL (not evaluable at 50/25 m).** No simulations were rerun; no commits or pushes were made.

Source runs: `study/250-d3-frozen-ref` at `afa02fa3e1165755bebe517a7b0b6a6573a51b6e`, source-built snapy **v2.10.34-6-gafa02fa**, kintera **2.5.13**. This uses the original D3 matrix, not the subsequent unchanged-harness reproduction.

Definition: theta′ = saved theta − 300 K; its minimum is over the whole domain. Front is the largest linearly interpolated crossing of theta′ = −1 K in the lowest vertical row, searching all adjacent horizontal samples. Interpolation is recomputed in float64 directly from NetCDF values.

Timing limitation: the existing driver writes the nominal 900 s snapshot at the first completed step at/after 900 s; the actual times are shown below (900.0086–900.1996 s). There are no exact-900 s snapshots. These nominal-900 s outputs are used as requested; no temporal interpolation or rerun was performed. The two local_polytrope failures have only their initial output, so their 900 s values are missing and not evaluable.

| Form | Grid (m) | Saved time (s) | Front (m) | min theta′ (K) |
|---|---:|---:|---:|---:|
| smooth5 | 100 | 900.199585 | 15245.673169 | -9.59054565 |
| smooth5 | 50 | 900.115234 | 15381.709265 | -9.71331787 |
| smooth5 | 25 | 900.056946 | 15400.648918 | -9.72955322 |
| isentrope | 100 | 900.065369 | 15244.049436 | -9.55374146 |
| isentrope | 50 | 900.008606 | 15383.115072 | -9.69906616 |
| isentrope | 25 | 900.034912 | 15401.243930 | -9.72561646 |
| none | 100 | 900.140564 | 15232.895361 | -9.54434204 |
| none | 50 | 900.018311 | 15376.864698 | -9.69412231 |
| none | 25 | 900.035400 | 15400.697565 | -9.72506714 |
| local_polytrope | 100 | 900.049255 | 15614.637002 | -10.66888428 |
| local_polytrope | 50 | absent; abort 819.064 | not evaluable | not evaluable |
| local_polytrope | 25 | absent; abort 798.437 | not evaluable | not evaluable |
| frozen | 100 | 900.122437 | 15343.052228 | -9.50732422 |
| frozen | 50 | 900.026123 | 15413.433273 | -9.68576050 |
| frozen | 25 | 900.038879 | 15407.104012 | -9.72244263 |

Rule: **(a)** |theta′min(25)+9.77| ≤ 0.10 K; **(b)** |front(25)−15537.44| ≤ 150 m; **(c)** both absolute 50→25 m changes are strictly smaller than the corresponding 100→50 m changes. All three are required. This replaces the previous monotone-reference-error/spread criterion for this re-score.

D3 O4 smooth5: a 0.04044678 K ≤ 0.10; b 136.791082 m ≤ 150; c front 18.939653 < 136.036097 m, theta′ 0.01623535 < 0.12277222 K — PASS.

D3 O4 isentrope: a 0.04438354 K ≤ 0.10; b 136.196070 m ≤ 150; c front 18.128858 < 139.065636 m, theta′ 0.02655029 < 0.14532471 K — PASS.

D3 O4 none: a 0.04493286 K ≤ 0.10; b 136.742435 m ≤ 150; c front 23.832867 < 143.969336 m, theta′ 0.03094482 < 0.14978027 K — PASS.

D3 O4 local_polytrope: a not evaluable; b not evaluable; c not evaluable (50/25 m aborted before 900 s) — FAIL.

D3 O4 frozen: a 0.04755737 K ≤ 0.10; b 130.335988 m ≤ 150; c front 6.329260 < 70.381044 m, theta′ 0.03668213 < 0.17843628 K — PASS.

Comparison with d3_report: all **13** evaluable theta′ minima match exactly. Front values agree within **0.000480249 m**; the sub-millimetre differences are from recomputing interpolation in float64 instead of the previous float32 array arithmetic. No score changes depend on these differences. Frozen rounds to **15343.05 / 15413.43 / 15407.10 m** and **−9.50732 / −9.68576 / −9.72244 K**, matching the quoted values.

Context only, supplied by the requester and not used for scoring: Athena smooth5 at 25 m, front 15419.2 m and min theta′ −9.750 K; Sridhar et al. (2022) front spread, 50 m 14767–15027 m and 100 m 14325–14669 m. No per-code Straka (1993) min-theta′ spread is used or quoted.

Recomputation: [rescore_o4.py](/mnt/data1/chengcli/ai_workspace/worker2/d3_study/rescore_o4.py); full precision data: [o4_rescore.json](/mnt/data1/chengcli/ai_workspace/worker2/d3_study/o4_rescore.json).
