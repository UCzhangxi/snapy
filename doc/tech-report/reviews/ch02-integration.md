# Chapter 2 integration handoff

Frozen rules reserve the chapter files and `_quarto.yml` to the editor. They do not exist at this base.
The author supplies `_opening.qmd` and these scheme includes for the editor's Chapter 2 file:

```markdown
# Governing equations and thermodynamics {#sec-ch02}

{{< include 02-thermodynamics/_opening.qmd >}}
{{< include 02-thermodynamics/_laws.qmd >}}
{{< include 02-thermodynamics/_interface.qmd >}}
{{< include 02-thermodynamics/_ideal-gas.qmd >}}
{{< include 02-thermodynamics/_ideal-moist.qmd >}}
{{< include 02-thermodynamics/_moist-mixture.qmd >}}
{{< include 02-thermodynamics/_aneos.qmd >}}
{{< include 02-thermodynamics/_shallow-water.qmd >}}
{{< include 02-thermodynamics/_consistency.qmd >}}
{{< include 02-thermodynamics/_saturation.qmd >}}
```

Include `15-verification/_ch02-thermodynamics.qmd` in Chapter 15. Add the report `src` directory to the Python
module path in the editor's package configuration. The local figstyle is copied unchanged from the
frozen common style; reconcile it with the incoming skeleton's shared module.
No editor-owned chapter file, rules pin, bibliography or Quarto config was modified.

Chapter 15 placement: OUTLINE.md:4848-4851 at `4b6c2041eca0ed4a2abbedeb4be2290553f086db` names “Verification catalogue”;
STYLE.md:365-370 at that same commit prescribes `book/chapters/NN-slug/_<scheme>.qmd`.
Neither specifies a literal slug. `15-verification/` is the chosen consistent spelling, not an exact
path quoted from OUTLINE. The editor must confirm it when integrating the book.
