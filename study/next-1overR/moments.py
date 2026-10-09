"""sympy: the x1 moments behind the 1/R term (README section 2).
  S1  x1v - rbar for the r^2 cell measure, exact and to O(h^4);
  S2  snapy's x1 face formulas on r^2 averages return the value at r_f + delta_v:
      the 5-point upwind (WENO5 smooth limit), the six-cell central mean, and the
      two-face hydrostatic scan + top anchor;
  S3  the x1 pressure force: -(p+ - p-)/dx1f  vs  the r^2 mean of -d_r p."""
import sympy as sp

r, rb, h, x, g = sp.symbols("r rbar h x g", positive=True)
c = sp.symbols("c0:7")
poly = sum(c[n] * (r - rb) ** n for n in range(7))      # generic smooth profile about rbar


def r2mean(f, lo, hi):
    return sp.integrate(f * r**2, (r, lo, hi)) / sp.integrate(r**2, (r, lo, hi))


# S1
rm, rp = rb - h / 2, rb + h / 2
x1v = sp.Rational(3, 4) * (rp**4 - rm**4) / (rp**3 - rm**3)
dv = sp.simplify(x1v - rb)
print("S1  x1v - rbar =", sp.factor(dv), " =", sp.series(dv, h, 0, 5).removeO())

# S2: face at r_f = rbar + h/2 between cell 0 = [rbar-h/2, rbar+h/2] and cell 1
rf = rb + h / 2
cells = {k: r2mean(poly, rb + (k - sp.Rational(1, 2)) * h, rb + (k + sp.Rational(1, 2)) * h)
         for k in range(-2, 4)}
up5 = sum(sp.Rational(w, 60) * cells[k] for w, k in zip((2, -13, 47, 27, -3), range(-2, 3)))
cp6 = sum(sp.Rational(w, 60) * cells[k] for w, k in zip((1, -8, 37, 37, -8, 1), range(-2, 4)))
exact = poly.subs(r, rf)
for name, val in (("upwind-5", up5), ("central-6", cp6)):
    err = sp.series(sp.simplify((val - exact).subs(rb, 1 / x)), h, 0, 4).removeO()
    lead = sp.simplify(err.coeff(h, 2).subs(x, 1 / rb))
    print(f"S2  {name}: face value - a(r_f) = h^2 * [{sp.factor(lead)}] + O(h^3)"
          "   (c1 = a'; = delta_v a')")
# scan: p_{i-1/2} - p_{i+1/2} = g rho_c h, rho_c the r^2 mean; truth g int rho dr
rhop = sum(sp.symbols(f"d{n}") * (r - rb) ** n for n in range(4))
scan = g * h * r2mean(rhop, rm, rp)
truth = g * sp.integrate(rhop, (r, rm, rp))
print("S2  scan step - exact step =", sp.factor(sp.series(scan - truth, h, 0, 4).removeO()),
      "  (= g h delta_v rho', so the scanned faces sit at r_f + delta_v)")

# S3: r^2 mean of -dp/dr vs the code's -(p+ - p-)/h
force_exact = r2mean(-sp.diff(poly, r), rm, rp)
force_code = -(poly.subs(r, rp) - poly.subs(r, rm)) / h
print("S3  code - exact pressure force =",
      sp.factor(sp.series(force_code - force_exact, h, 0, 4).removeO()),
      "  (c2 = p''/2: = +delta_v p'' + O(h^4))")
