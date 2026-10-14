import sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage
x1,y1=45.9,70; G=0.05
for name in sys.argv[1:]:
    d=np.load('img/step05/card_free_%s.npz'%name)
    blk,f0,f90,net=d['blk'],d['free0'],d['free90'],d['net']
    lab,n=ndimage.label(f0|f90)
    print(name,'free0',f0.sum(),'free90',f90.sum(),'regions',n)
    ys,xs=np.nonzero(net)
    for k in range(1,n+1):
        yy,xx=np.nonzero(lab==k)
        cx,cy=x1+G*xx.mean(),y1+G*yy.mean()
        dmin=np.hypot(x1+G*xs[:,None]-cx, y1+G*ys[:,None]-cy).min() if len(xs) else -1
        print('   region %d: %d cells, centre (%.2f, %.2f), x %.2f-%.2f y %.2f-%.2f, %.1f mm from SCL/SDA copper'%(k,len(xx),cx,cy,x1+G*xx.min(),x1+G*xx.max(),y1+G*yy.min(),y1+G*yy.max(),dmin))
    img=np.ones(blk.shape+(3,)); img[blk]=(.75,.75,.75); img[net]=(.2,.3,1); img[f0]=(.1,.7,.1); img[f90&~f0]=(.6,.9,.2)
    fig=plt.figure(figsize=(10,10)); plt.imshow(img,extent=(x1,x1+G*blk.shape[1],y1+G*blk.shape[0],y1),interpolation='nearest')
    plt.xticks(np.arange(46,91,1)); plt.yticks(np.arange(70,116,1)); plt.grid(True,lw=.3); plt.tick_params(labelsize=5)
    plt.title('card %s: free centres (dark green 0 deg, light 90 deg); SCL/SDA copper blue'%name,fontsize=8)
    fig.savefig('img/step05/card_free_%s.png'%name,dpi=110,bbox_inches='tight'); plt.close(fig)
