"""Five cell integrals and six pressure faces, schematic index spacing."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig,ax=plt.subplots(figsize=(fs.DOUBLE,2.5))
    for i in range(6):
        ax.plot([i,i],[-.15,.15],color=fs.ORANGE,lw=2)
        ax.text(i,-.35,'p',ha='center',color=fs.BLACK)
    for i in range(5):
        ax.plot(i+.5,0,'o',color=fs.SKY)
        ax.text(i+.5,.3,'cell mean',ha='center',fontsize=8)
    ax.plot([0,5],[0,0],color=fs.BLACK,lw=.5)
    ax.text(2.5,.8,'five r-squared integrals determine a quartic',ha='center')
    ax.text(2.5,-.8,'six face pressures determine the source quintic',ha='center')
    ax.set(xlim=(-.5,5.5),ylim=(-1,1));ax.axis('off')
    return fig
