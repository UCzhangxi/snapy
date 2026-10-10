# Appendix integration

Base: `4b6c2041eca0ed4a2abbedeb4be2290553f086db`. Source pins are recorded in the appendix.
Under STYLE.md:365-370 the editor owns chapter files and the book configuration.
Create the appendix heading `# Components outside snapy {#sec-appe}` and include
`{{< include appe-components/_components.qmd >}}` in the appendix chapter file.
The literal appendix file slug is an integration choice; the fixed identifier is `appe`.

Scope: component roles, snapy call sites, C++ links, Python imports, declared version constraints and explicit gaps.
No numerical method is added, so no new derivation or runtime test is needed for this inventory.
The source-only audit cannot establish binary dependencies or a compatible dependency-version matrix.
Inherited frozen rules and source archives are not changed by this branch.
