import io, sys
WT = "/nobackupp19/xzhang11/apps/canoe/snapy-wbedit"

def patch(path, old, new):
    p = WT + path
    s = io.open(p, encoding="utf-8").read()
    n = s.count(old)
    assert n == 1, "expected 1 match in %s, found %d" % (path, n)
    io.open(p, "w", encoding="utf-8").write(s.replace(old, new))
    print("patched", path)

# --- Patch A: distributed x1 reference scan in _hydro_ref_x1 (hydro.cpp) ---
patch("/src/hydro/hydro.cpp",
"""  auto cum_iu = cum.select(-1, iu).unsqueeze(-1);  // [nc3,nc2,1]
  auto psf_lo = anchor + cum_iu - cum + dp;  // pressure at lower face of cell i
  auto psf_hi = psf_lo - dp;                 // pressure at upper face of cell i
""",
"""  auto cum_iu = cum.select(-1, iu).unsqueeze(-1);  // [nc3,nc2,1]

  // Global x1 reference across a vertical (nb1>1) decomposition: make the
  // hydrostatic reference continuous over the x1 process seams. The block
  // owning x1-outer anchors at the true domain top; every block below receives
  // the running seam-face pressure from the block above and passes on that
  // value plus its own interior hydrostatic drop (= its bottom-face pressure).
  // A serial top->bottom scan along the x1 process column. nb1 == 1 (no x1
  // neighbor) => A == anchor, bit-identical to the single-block reference.
  auto A = anchor;
  auto layout = pmb->get_layout();
  if (layout && layout->has_process_group()) {
    auto iloc = layout->loc_of(layout->options->rank());
    int above = layout->neighbor_rank(iloc, {0, 0, 1});   // toward x1-outer
    int below = layout->neighbor_rank(iloc, {0, 0, -1});  // toward x1-inner
    constexpr int kWbRefTag = 0x7715;
    if (above >= 0) {
      std::vector<torch::Tensor> rbuf = {torch::empty_like(anchor)};
      layout->comm->recv(rbuf, above, kWbRefTag)->wait();
      A = rbuf[0];
    }
    if (below >= 0) {
      std::vector<torch::Tensor> sbuf = {
          A + dp.narrow(-1, is, iu - is + 1).sum(-1, /*keepdim=*/true)};
      layout->comm->send(sbuf, below, kWbRefTag)->wait();
    }
  }

  auto psf_lo = A + cum_iu - cum + dp;  // pressure at lower face of cell i
  auto psf_hi = psf_lo - dp;                 // pressure at upper face of cell i
""")

# --- Patch B: relax wb_x1 gate; drop the disable warning (hydro_forward.cpp) ---
patch("/src/hydro/hydro_forward.cpp",
"""    // x1 column (references are integrated per block; an internal x1 seam
    // would get inconsistent references from its two neighbors).
    bool wb_x1 = grav1 && w.size(0) > IPR &&
                 options->eos()->type() != "shallow-water" && phys_x1inner &&
                 phys_x1outer;
    if (grav1 && !wb_x1 && !(phys_x1inner && phys_x1outer)) {
      TORCH_WARN_ONCE(
          "[Hydro] well-balanced x1 reconstruction disabled: the block does "
          "not own the full x1 column (nb1 > 1); hydrostatic references "
          "cannot span an internal x1 seam.");
    }
""",
"""    // x1 column, OR it spans a vertical (nb1>1) decomposition -- in which case
    // _hydro_ref_x1 makes the reference continuous across the x1 process seams
    // with a distributed scan, so WB now engages under x1 decomposition too.
    bool wb_x1 = grav1 && w.size(0) > IPR &&
                 options->eos()->type() != "shallow-water";
""")

# --- Patch C: apply even-parity ghost fill only at PHYSICAL x1 walls ---
patch("/src/hydro/hydro_forward.cpp",
"""        for (int c : {(int)IPR, (int)IDN}) {
          w_work[c]
              .narrow(-1, is - ng, ng)
              .copy_(w_work[c].narrow(-1, is, ng).flip(-1));
          w_work[c]
              .narrow(-1, iu + 1, ng)
              .copy_(w_work[c].narrow(-1, iu + 1 - ng, ng).flip(-1));
        }
""",
"""        // Only at PHYSICAL x1 walls. At an internal seam (nb1>1) the ghost
        // perturbation must come from the neighbor (already halo-exchanged),
        // not a mirror of this block's own interior.
        for (int c : {(int)IPR, (int)IDN}) {
          if (phys_x1inner)
            w_work[c]
                .narrow(-1, is - ng, ng)
                .copy_(w_work[c].narrow(-1, is, ng).flip(-1));
          if (phys_x1outer)
            w_work[c]
                .narrow(-1, iu + 1, ng)
                .copy_(w_work[c].narrow(-1, iu + 1 - ng, ng).flip(-1));
        }
""")
print("ALL PATCHES OK")
