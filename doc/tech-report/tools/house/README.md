# House render-gate scripts (imported unchanged, to be adapted)

These three scripts are the render gate of the project owner's Quarto books, copied unchanged. STYLE.md section 10.9
adopts them. They are not wired to this report yet: paths, the book-specific table renderer named in
`render_gate.py`, and the chapter list check need adapting. The CI owner adapts them into `tools/` and deletes this
folder in the same commit.

- `render_gate.py`: renders, keeps the LuaLaTeX log, and fails on missing characters, duplicate labels, unresolved
  cross-references, unrendered math in table cells and the other checks listed in its docstring.
- `check_table_cells.py`: scans rendered table cells for literal LaTeX and unresolved references.
- `check_math_spans.py`: checks inline and display math spans in the `.qmd` sources.
