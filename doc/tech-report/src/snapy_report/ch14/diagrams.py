"""Boundary stencils and ownership cartoons; no solver measurements."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from snapy_report import figstyle as fs


def boxes(ax, labels, ghost=()):
    for i,label in enumerate(labels):
        color=fs.PURPLE if i in ghost else fs.SKY
        ax.add_patch(Rectangle((i,0),1,1,fill=False,edgecolor=color,lw=1.7))
        ax.text(i+.5,.5,label,ha='center',va='center',fontsize=9)
    ax.set(xlim=(-.2,len(labels)+.2),ylim=(-.5,1.7));ax.axis('off')


def arrow(ax,start,end,label='',y=1.25):
    ax.annotate('',xy=(end+.5,y),xytext=(start+.5,y),
                arrowprops=dict(arrowstyle='->',color=fs.GREEN))
    if label:ax.text((start+end+1)/2,y+.09,label,ha='center',fontsize=8)


def flow(labels):
    fs.apply();fig,ax=plt.subplots(figsize=(fs.DOUBLE,.6*len(labels)+.4))
    ax.set(xlim=(0,1),ylim=(-.4,len(labels)));ax.axis('off')
    for i,label in enumerate(labels):
        y=len(labels)-1-i
        ax.text(.5,y,label,ha='center',va='center',fontsize=9,
                bbox=dict(boxstyle='round,pad=.4',facecolor='white',edgecolor=fs.GREEN))
        if i<len(labels)-1:ax.annotate('',xy=(.5,y-.72),xytext=(.5,y-.28),arrowprops=dict(arrowstyle='->'))
    fig.tight_layout();return fig


def make_stencil(kind):
    fs.apply()
    if kind=='timing':
        return flow(['block: exchange hydro + scalars','received tangential ghost strip',
                     'x1 wall callback on strip; skip outflow','reconstruct / advance / RK / solid refill',
                     'last-stage adjustment and enabled fixer','physical fills'])
    if kind=='registry':
        fig,ax=plt.subplots(figsize=(fs.DOUBLE,3))
        ax.add_patch(Rectangle((.3,.25),.4,.5,fill=False,lw=1.5))
        for x,y,s in [(.5,.13,'x1 inner: reflecting'),(.5,.88,'x1 outer: outflow'),
                      (.12,.5,'x2 inner\nexchange'),(.88,.5,'x2 outer\nwrapped'),
                      (.5,.55,'owned block'),(.5,.37,'x3 pair: front / back')]:
            ax.text(x,y,s,ha='center',va='center',fontsize=9)
        ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    elif kind in ('reflecting','periodic','extrapolation','custom'):
        fig,ax=plt.subplots(figsize=(fs.DOUBLE,2.1))
        labels={'reflecting':['q2\n-v2','q1\n-v1','q1\nv1','q2\nv2','q3\nv3','q4\nv4'],
                'periodic':['q3','q4','q1','q2','q3','q4'],
                'extrapolation':['q1','q1','q1','q2','q3','q4'],
                'custom':['unchanged\nor 1','unchanged\nor 1','owned','owned','owned','owned']}[kind]
        boxes(ax,labels,ghost=(0,1));ax.plot([2,2],[-.1,1.05],color=fs.BLACK,lw=2)
        ax.text(.9,-.27,'ghosts',ha='center',color=fs.PURPLE)
        ax.text(4,-.27,'owned cells',ha='center')
        if kind=='reflecting':arrow(ax,3,0,'mirror');arrow(ax,2,1,y=1.05)
        elif kind=='periodic':arrow(ax,4,0,'wrap');arrow(ax,5,1,y=1.05)
        elif kind=='extrapolation':arrow(ax,2,0,'repeat nearest');arrow(ax,2,1,y=1.05)
        else:ax.text(3,1.4,'custom: identity; solid mask: literal one',ha='center')
    elif kind=='outflow':
        fig,axs=plt.subplots(1,2,figsize=(fs.DOUBLE,3.2));ax=axs[0]
        ax.axvline(0,color=fs.BLACK);ax.set(xlim=(-1,1),ylim=(0,1.2),xlabel='outward distance (schematic)',ylabel='time (schematic)')
        for speed,label in [(-.7,'incoming: zero'),(.25,'advected'),(.9,'outgoing acoustic')]:
            ax.annotate('',xy=(speed,1),xytext=(0,0),arrowprops=dict(arrowstyle='->',color=fs.GREEN if speed>=0 else fs.PURPLE))
            ax.text(speed,1.06,label,ha='center',fontsize=7)
        ax=axs[1];ax.set(xlim=(-.1,1.25),ylim=(-.1,1.25),xlabel='component perturbation (scaled)',ylabel='second component (scaled)')
        ax.add_patch(Rectangle((0,0),.85,1,fill=False,edgecolor=fs.BLUE))
        ax.plot([.2,1.1],[.2,.9],color=fs.BLACK,ls=':')
        ax.plot(.2,.2,'o',color=fs.BLUE,label='background')
        ax.plot(1.1,.9,'x',color=fs.VERMILLION,label='unlimited')
        ax.plot(.82,.682,'s',color=fs.GREEN,label='shared contraction')
        ax.legend(fontsize=7,loc='upper left')
    elif kind=='exchange':
        fig,axs=plt.subplots(2,1,figsize=(fs.DOUBLE,3.5))
        boxes(axs[0],['panel A','edge donor','halo donor','panel B ghosts'],ghost=(2,3))
        arrow(axs[0],2,3,'interpolate + frame transform')
        boxes(axs[1],['factor A','donor factor','raw copy','factor B'],ghost=(2,))
        arrow(axs[1],1,2,'scalar raw copy')
        axs[1].text(2,-.35,'corner = average of adjacent edge strips',ha='center',fontsize=8)
    elif kind=='solids':
        fig,axs=plt.subplots(1,2,figsize=(fs.DOUBLE,3.3));ax=axs[0]
        for j in range(4):
            for i in range(4):
                solid=i>=2 and j<2
                ax.add_patch(Rectangle((i,j),1,1,facecolor=fs.GREY if solid else 'white',edgecolor=fs.BLACK))
                ax.text(i+.5,j+.5,'S' if solid else 'F',ha='center',va='center')
        ax.annotate('',xy=(1.95,.5),xytext=(1.2,.5),arrowprops=dict(arrowstyle='<->',color=fs.GREEN))
        ax.set(xlim=(0,4),ylim=(0,4),aspect='equal');ax.axis('off');ax.set_title('Staircase: F fluid, S solid')
        ax=axs[1];boxes(ax,['1','0','0','1','1'],ghost=())
        ax.text(2.5,1.45,'thin fluid run: 10011',ha='center')
        ax.text(2.5,-.3,'minimum repair: 11111 (two flips)',ha='center',fontsize=8)
    elif kind=='wb':
        fig,axs=plt.subplots(2,1,figsize=(fs.DOUBLE,3.4))
        x=np.arange(-2,4);truth=2+.15*x
        axs[0].plot(x,truth,'o-',color=fs.BLUE,label='linear continuation')
        axs[0].plot(x,np.where(x<0,2,truth),'s--',color=fs.VERMILLION,label='repeated wall cell')
        axs[0].axvline(-.5,color=fs.BLACK);axs[0].set(xlabel='cell index',ylabel='scaled density / pressure');axs[0].legend(fontsize=8)
        boxes(axs[1],["p'=0","p'=0","p'=0","p'=0","p'=0","p'=0"],ghost=(0,1))
        axs[1].plot([2,2],[0,1],color=fs.BLACK,lw=2);arrow(axs[1],3,0,'even perturbation mirror')
    else:raise ValueError(kind)
    fig.tight_layout();return fig


def dependencies():
    return flow(['registry / physical-face classification',
                 'physical fill requires callback and representation',
                 'outflow requires saved background + EOS + coordinates',
                 'exchange then corner refresh requires idempotent wall fill',
                 'solid VIC closure requires unsplit x1 column',
                 'WB perturbation mirror excludes outflow; reference clamp differs'])
