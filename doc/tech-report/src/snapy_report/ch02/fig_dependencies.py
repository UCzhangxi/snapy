"""Chapter 2 structural dependencies at snapy e894700ff7aee30b52882e5202b16461413780b0; no data."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.5))
    nodes = {"EOS interface": (.1,.5), "ideal gas": (.42,.9), "ideal moist": (.42,.65),
             "moist mixture": (.42,.4), "ANEOS / shallow": (.42,.15), "consistency": (.77,.8),
             "phase equilibrium": (.8,.35)}
    for label, (x,y) in nodes.items():
        ax.text(x,y,label,ha="center",va="center",fontsize=8,bbox=dict(fc="white",ec=fs.BLACK))
    for name in ("ideal gas","ideal moist","moist mixture","ANEOS / shallow"):
        ax.annotate("",xy=nodes[name],xytext=nodes["EOS interface"],arrowprops=dict(arrowstyle="->",color=fs.BLACK,shrinkA=32,shrinkB=42))
    ax.text(.68,.53,"requires thermo",fontsize=8)
    ax.annotate("",xy=nodes["phase equilibrium"],xytext=nodes["moist mixture"],arrowprops=dict(arrowstyle="->",color=fs.GREEN,shrinkA=42,shrinkB=50))
    ax.set(xlim=(-.08,1.05),ylim=(0,1)); ax.axis("off")
    return fig
