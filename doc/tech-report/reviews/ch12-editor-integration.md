# Configuration chapter integration

Frozen rules: `4b6c2041eca0ed4a2abbedeb4be2290553f086db`. Code pin: `e894700ff7aee30b52882e5202b16461413780b0`.
The editor owns chapter files and the book configuration (STYLE.md:365–370 at the frozen rules).
Create the chapter heading `# Build-time and run-time switches and configurations {#sec-ch12}`, then include:

```markdown
{{< include 12-configuration/_opening.qmd >}}
{{< include 12-configuration/_build.qmd >}}
{{< include 12-configuration/_macros.qmd >}}
{{< include 12-configuration/_environment.qmd >}}
{{< include 12-configuration/_wb-reference.qmd >}}
{{< include 12-configuration/_centroid.qmd >}}
{{< include 12-configuration/_flux-covariance.qmd >}}
{{< include 12-configuration/_mass-covariance.qmd >}}
{{< include 12-configuration/_radial-exact.qmd >}}
{{< include 12-configuration/_layout.qmd >}}
{{< include 12-configuration/_test-environment.qmd >}}
{{< include 12-configuration/_yaml.qmd >}}
{{< include 12-configuration/_matrix.qmd >}}
```

Include `15-verification/_ch12-configuration.qmd` in Chapter 15.
OUTLINE.md:4848–4851 at the frozen rules names the Verification catalogue;
STYLE.md:365–370 prescribes the generic directory pattern, but neither fixes the literal slug.
`15-verification` matches the accompanying chapter fragments and awaits editor integration.
Do not edit the frozen planning sources as part of this chapter.

No official citation checker or book configuration exists at the frozen rules. Quarto is unavailable locally.
Local checks are not a substitute for an HTML/PDF render or the official citation gate.
