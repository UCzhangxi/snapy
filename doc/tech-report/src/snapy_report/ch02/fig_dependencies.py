"""Chapter 2 structural dependencies at snapy 6fbb39750f62b83df096058a4746e77d0a634bc5; no data."""
from snapy_report import figstyle as fs


def make_fig():
    fig, ax = fs.new_figure(fs.DOUBLE, 2.5)
    nodes = {"EOS interface": (.1,.5), "ideal gas": (.42,.9), "ideal moist": (.42,.65),
             "moist mixture": (.42,.4), "ANEOS / shallow": (.42,.15), "consistency": (.77,.8),
             "phase equilibrium": (.8,.35)}
    for label, (x,y) in nodes.items():
        ax.text(x,y,label,ha="center",va="center",fontsize=fs.SMALL_PT,bbox=dict(fc="white",ec=fs.BLACK))
    for name in ("ideal gas","ideal moist","moist mixture","ANEOS / shallow"):
        ax.annotate("",xy=nodes[name],xytext=nodes["EOS interface"],arrowprops=dict(arrowstyle="->",color=fs.BLACK,shrinkA=32,shrinkB=42))
    ax.text(.68,.53,"requires thermo",fontsize=fs.SMALL_PT)
    ax.annotate("",xy=nodes["phase equilibrium"],xytext=nodes["moist mixture"],arrowprops=dict(arrowstyle="->",color=fs.GREEN,shrinkA=42,shrinkB=50))
    ax.set(xlim=(-.08,1.05),ylim=(0,1)); ax.axis("off")
    return fig
