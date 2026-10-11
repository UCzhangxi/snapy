"""Which conserved quantity each conservation test asserts, and to what tolerance, read from the test sources of
snapy@e894700ff7aee30b52882e5202b16461413780b0 (tests/). A table drawn as a matrix; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs

COLS = ["mass", "species", "energy", "momentum", "E+PE", "tracer"]
ROWS = [  # test, {column: tolerance text}
    ("test_condensate_conservation", {"species": "1e-12"}),
    ("test_fix_vapor_volume", {"species": "1e-12"}),
    ("test_parentless_cloud (+nb1, mp)", {"species": "1e-12"}),
    ("test_vapor_column_nb1", {"species": "1e-12"}),
    ("test_wall_saturation", {"species": "1e-12", "energy": "1e-12"}),
    ("test_flux_positivity_python", {"species": "1e-12", "tracer": "1e-12"}),
    ("test_flux_positivity_cubedsphere", {"tracer": "1e-13"}),
    ("test_flux_positivity_cubedsphere_moist", {"species": "1e-13"}),
    ("test_flux_positivity_carry", {"energy": "1e-12", "momentum": "1e-12"}),
    ("test_flux_covariance_seams_python", {"mass": "1e-12", "species": "1e-12", "E+PE": "1e-12"}),
    ("test_tracer_dry_convention_python", {"tracer": "1e-12"}),
    ("run_example_mass_check.py *", {"mass": "1e-8"}),
]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.4))
    ax.set_axis_off()
    x0, w = 3.9, 0.75
    for j, c in enumerate(COLS):
        ax.text(x0 + w * j + w / 2, len(ROWS) + 0.3, c, ha="center", fontsize=7.5, weight="bold")
    for i, (name, cells) in enumerate(ROWS):
        y = len(ROWS) - 1 - i
        grey = name.endswith("*")
        ax.text(0.0, y + 0.4, name, fontsize=6.5, family="monospace", va="center",
                color=fs.GREY if grey else fs.BLACK)
        for j, c in enumerate(COLS):
            if c in cells:
                ax.add_patch(plt.Rectangle((x0 + w * j + 0.04, y + 0.06), w - 0.08, 0.68,
                                           fc=fs.GREY if grey else fs.GREEN, ec="none", alpha=0.75))
                ax.text(x0 + w * j + w / 2, y + 0.4, cells[c], ha="center", va="center", fontsize=6.5)
            else:
                ax.add_patch(plt.Rectangle((x0 + w * j + 0.04, y + 0.06), w - 0.08, 0.68, fc="none",
                                           ec="#DDDDDD", lw=0.5))
    ax.set_xlim(-0.05, x0 + w * len(COLS) + 0.05)
    ax.set_ylim(-0.1, len(ROWS) + 0.8)
    return fig
