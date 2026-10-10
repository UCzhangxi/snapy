"""Dependency edges, not numerical measurements."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.8))
    ax.text(.1,.5,'snapy',ha='center',va='center',bbox=dict(boxstyle='round',fc=fs.SKY))
    for y,label,edge,style in [(.85,'kintera','thermodynamics / kinetics','-'),
                               (.5,'pyharp','stage integration','-'),
                               (.15,'Disort','PUBLIC C++ link','--')]:
        ax.text(.82,y,label,ha='center',va='center',bbox=dict(boxstyle='round',fc=fs.GREEN))
        ax.annotate('',xy=(.73,y),xytext=(.18,.5),arrowprops=dict(arrowstyle='->',linestyle=style))
        ax.text(.47,(y+.5)/2+.10,edge,ha='center',fontsize=8)
    ax.text(.5,-.05,'Python imports: kintera, pyharp, pydisort',ha='center',fontsize=9)
    ax.set(xlim=(0,1),ylim=(-.15,1));ax.axis('off')
    return fig
