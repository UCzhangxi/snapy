"""Five-cell filter and one-sided wall continuation."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig,ax=plt.subplots(figsize=(fs.DOUBLE,2.6))
    for i,w in zip(range(-2,3),[-1,4,10,4,-1]):
        ax.plot(i,0,'o',color=fs.SKY,ms=9)
        ax.text(i,.24,str(w)+'/16',ha='center')
        ax.text(i,-.24,'i'+(f'{i:+}' if i else ''),ha='center')
        ax.plot([i-.5,i-.5],[-.1,.1],color=fs.BLACK)
    ax.plot([-2.5,2.5],[0,0],color=fs.BLACK,lw=.6)
    ax.text(0,.65,'cell-ratio filter; interior offsets in cell widths',ha='center')
    ax.text(0,-.65,'wall ghosts from owned cells: (4,-6,4,-1) and (10,-20,15,-4)',ha='center',fontsize=8)
    ax.set(xlim=(-3,3),ylim=(-.9,.9));ax.axis('off')
    return fig
