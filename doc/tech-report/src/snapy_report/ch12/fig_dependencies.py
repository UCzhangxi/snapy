"""Logical dependencies: separately labelled edges, not a sequential flow."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig,ax=plt.subplots(figsize=(fs.DOUBLE,3.4))
    nodes={'XC':(.1,.85),'WB':(.38,.85),'3 ghosts\nif gravity':(.77,.85),
           'MC':(.1,.52),'3 owned cells\nif gravity':(.5,.52),
           'RE':(.1,.18),'face mode + gravity\nCartesian / spherical':(.55,.18)}
    for label,(x,y) in nodes.items():
        ax.text(x,y,label,ha='center',va='center',fontsize=9,
                bbox=dict(boxstyle='round',fc=fs.GREEN if label in ('XC','WB','MC','RE') else 'white',ec=fs.BLACK))
    for start,end,label,y in [('XC','WB','implies',.85),('WB','3 ghosts\nif gravity','requires',.85),
                               ('MC','3 owned cells\nif gravity','requires',.52),
                               ('RE','face mode + gravity\nCartesian / spherical','acts only with',.18)]:
        x0=nodes[start][0]+.04; x1=nodes[end][0]-.12
        ax.annotate('',xy=(x1,y),xytext=(x0,y),arrowprops=dict(arrowstyle='->'))
        ax.text((x0+x1)/2,y+.06,label,ha='center',fontsize=8)
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    return fig
