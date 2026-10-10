# Chapter 6. Gravity and energy

How the work done by gravity enters snapy's energy equation, and what each form of it conserves. Pinned sha:
snapy `dae902b`. Plan: `OUTLINE.md` chapter 6.

| section | file | status |
|---|---|---|
| 6.1 Constant gravity forcing and the cell form (`gravity-work: cell`, the default) | `cell_work.md` | outline only |
| 6.2 The face form, `face-wallc`, and the cp3/cp5/weno5 curvature flux | `face_work.md` | outline only |
| 6.3 The gravity-work fixer | `fixer.md` | outline only |
| 6.4 The corrected-PE face work, scheme D (`SNAP_GRAVITY_WORK_RADIAL_EXACT`) | `D_face_work_pe.md` | **draft, all six layers: the model section** |
| 6.5 Gravity work inside the vertical implicit operator | `vic_gravity_work.md` | outline only |
| 6.6 What each form conserves | `invariants.md` | outline only |

Reading order: 6.1 → 6.2 → 6.3, then 6.4, then 6.5 and 6.6. Section 6.4 is written first because it is the
template every chapter author copies. It refers forward to 6.1-6.3 for the cell and face forms.

Supporting files:
- `checks/d_face_work_pe_check.py` (+ `.out`, `.json`): the executable check of 6.4. Run with `python3`.
- `figures/fig_D_face_work_pe.py` (+ `.png`): Figure 6.4.1. It reads the check's `.json`, so run the check first
  when the formulas change.
- Shared figure style: `../common/figstyle.py`.

Rebuild everything in this chapter:

```
python3 checks/d_face_work_pe_check.py > checks/d_face_work_pe_check.out
python3 figures/fig_D_face_work_pe.py
python3 ../../build/check_citations.py D_face_work_pe.md
```
