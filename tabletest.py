import numpy as np
import matplotlib.pyplot as plt
import time
import redpy

from tables import *
from redpy.optics import *
from obspy import UTCDateTime


"""
Test script for PyTables functionality
"""

opt = redpy.config.Options(filename="test.h5")

redpy.table.initializeTable(opt) 

t = UTCDateTime("2004-09-23")
st = redpy.trigger.getIRIS(t, opt, nsec=86400)
temptrig = redpy.trigger.trigger(st, opt)

# Clean out data spikes and calibration pulses
trigs, junk = redpy.trigger.dataclean(temptrig,opt)

h5file = open_file(opt.filename, "a")
rtable = eval('h5file.root.'+ opt.groupName + '.repeaters')

#Filters the data and populates new row in Repeater catalog table with FFT and COEFF
for i in range(len(trigs)):
    redpy.table.populateRepeater(rtable, i, trigs[i], opt)

# Write to disk
rtable.flush()

# Need to update this section...

ctable = eval('h5file.root.' + opt.groupName + '.correlation')

t = time.time()
for i in range(len(rtable)):
    print("{0} of {1}".format(i,len(rtable)))
    ci = '(id == {})'.format(i)
    cj = '(id < {})'.format(i)
    
    ti = rtable.where(ci)
    tj = rtable.where(cj)

    for ri in ti:
        fft1 = ri['windowFFT']
        coeff1 = ri['windowCoeff']

    Ctmp = np.zeros((i+1,))
    Ltmp = np.zeros((i+1,))
    for rj in tj:
        fft2 = rj['windowFFT']
        coeff2 = rj['windowCoeff']
        j = rj['id']
        Ctmp[j], Ltmp[j] = redpy.correlation.xcorr1x1(fft1, fft2, coeff1, coeff2)

    if max(Ctmp) > 0.65:

        jmax = np.argmax(Ctmp)
        ti = rtable.where(ci)
        tj = rtable.where(cj)

        for ri in ti:
            ri['windowStart'] = ri['windowStart'] + Ltmp[jmax]
            ri['windowCoeff'], ri['windowFFT'] = redpy.correlation.calcWindow(ri['waveform'],
                ri['windowStart'], opt)
            ri.update()
            coeff1 = ri['windowCoeff']
            fft1 = ri['windowFFT']

        for rj in tj:
            fft2 = rj['windowFFT']
            coeff2 = rj['windowCoeff']
            j = rj['id']
            Ctmp[j], Ltmp[j] = redpy.correlation.xcorr1x1(fft1, fft2, coeff1, coeff2)

    for j in range(0, i+1):
        if Ctmp[j] > 0.7:
            redpy.table.appendCorrelation(ctable, i, j, Ctmp[j], opt)

    ctable.flush()
            

print("Correlation done in: {:03.2f} seconds".format(time.time()-t))

C = np.zeros((len(rtable),len(rtable)))
C[ctable.cols.id1[:], ctable.cols.id2[:]] = ctable.cols.ccc[:]
C = C + C.T + np.eye(len(C))

# Copied from old stuff:
maxes = np.max(C - np.eye(len(C)), axis=0)
print("Orphans: {:.2%}".format(1.0* len(maxes[maxes<0.65]) / len(C)))

# Run OPTICS
redpy.cluster.runFullOPTICS(rtable, ctable)

order = rtable.cols.order[:]
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


# Plot unordered, unaligned waveforms
data = np.zeros((len(rtable), 2000))
fig = plt.figure(figsize=(12, 6))
for r in rtable.iterrows():
    n = r['id']
    data[n, :] = r['waveform'][500:2500]
    data[n, :] = data[n, :]/max(data[n, 500:1012])
ax = fig.add_subplot(1, 1, 1)
ax.imshow(data, aspect='auto', vmin=-1, vmax=1, interpolation='nearest', cmap='RdBu')

# Plot ordered, aligned waveforms
data = np.zeros((len(rtable), 2000))
fig = plt.figure(figsize=(12, 6))
for r in rtable.iterrows():
    n = r['id']
    data[n, :] = r['waveform'][r['windowStart']-500:r['windowStart']+1500]
    data[n, :] = data[n, :]/max(data[n, 500:1012])
datao = data[order, :]
ax = fig.add_subplot(1, 1, 1)
ax.imshow(datao, aspect='auto', vmin=-1, vmax=1, interpolation='nearest', cmap='RdBu')


plt.show()


# Close file when done
h5file.close()