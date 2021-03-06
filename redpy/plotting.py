from tables import *
import numpy as np
import matplotlib.pyplot as plt

"""
These are very brute force plotting; should be replaced with more sophisticated functions
"""


def createOrderedWaveformFigure(rtable, opt):
    data = np.zeros((len(rtable), int(20*opt.samprate)))
    fig = plt.figure(figsize=(12, 6))
    n=-1
    for r in rtable.iterrows():
        n = n+1
        data[n, :] = r['waveform'][r['windowStart']-int(
            5*opt.samprate):r['windowStart']+int(15*opt.samprate)]
        data[n, :] = data[n, :]/max(data[n, int(5*opt.samprate):int(
            5*opt.samprate)+opt.winlen])
    
    order = rtable.cols.order[:]
    datao = data[order, :]
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(datao, aspect='auto', vmin=-1, vmax=1, interpolation='nearest', cmap='RdBu')


def createCMatrixFigure(rtable, ctable):
    
    order = rtable.cols.order[:]
    
    C = np.zeros((len(rtable),len(rtable)))
    id1 = ctable.cols.id1[:]
    id2 = ctable.cols.id2[:]
    
    # Convert id to row
    rtable_ids = rtable.cols.id[:]
    r = np.zeros((max(rtable_ids)+1,)).astype('int')
    r[rtable_ids] = range(len(rtable_ids))
    C[r[id1], r[id2]] = ctable.cols.ccc[:]
    C = C + C.T + np.eye(len(C))
    Co = C[order, :]
    Co = Co[:, order]

    # Plot the C matrices (saturated below 0.65)
    # Left is ordered by time
    # Right is ordered by cluster ordering
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 2, 1)
    ax.imshow(C, aspect='auto', vmin=0.65, vmax=1, interpolation='nearest')
    ax = fig.add_subplot(1, 2, 2)
    ax.imshow(Co, aspect='auto', vmin=0.65, vmax=1, interpolation='nearest')


def createWigglePlot(jtable, opt):
    #waveform wiggle plot of input waveforms
    fig = plt.figure(figsize=(20, 15))
    n=0.
    for r in jtable.iterrows():
        dat=r['waveform']
        dat=dat/max(dat)
        tvec = np.arange(0,len(dat)*1/opt.samprate,1/opt.samprate)
        plt.plot(tvec,np.add(dat,n))
        n = n+3
    plt.ylabel('index')
    plt.xlabel('time(s)')
    #plt.title('Junk triggers')
    plt.autoscale(tight=True)
    plt.show()
