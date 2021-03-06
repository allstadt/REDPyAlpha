from tables import *
from redpy import *
import numpy as np
from scipy.fftpack import fft
from obspy import UTCDateTime
import time

"""
Test script for PyTables functionality
"""


initializeTable("hsr", "MSH: HSR-EHZ-UW", ["HSR", "EHZ", "UW", "--"],
    filename="test.h5") 

t = UTCDateTime("2004-09-24")
st = getIRIS(t, "HSR", "EHZ", "UW", nsec=3600)
trigs = trigger(st)
trigs = trigs[0:100]

h5file = open_file("test.h5", "a")
rtable = h5file.root.hsr.repeaters

wstart = 1000 # Manual definition of window for now

for i in range(len(trigs)):
    populateTrigger(rtable.row, i, trigs[i], wstart)

# Write to disk
rtable.flush()


# Need to update this section...

ctable = h5file.root.hsr.correlation
corr = ctable.row

t = time.time()
for i in range(len(rtable)):
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
        Ctmp[j], Ltmp[j] = xcorr1x1(fft1, fft2, coeff1, coeff2)

    if max(Ctmp) > 0.6:

        jmax = np.argmax(Ctmp)
        ti = rtable.where(ci)
        tj = rtable.where(cj)

        for ri in ti:
            ri['windowStart'] = ri['windowStart'] + Ltmp[jmax]
            ri['windowCoeff'], ri['windowFFT'] = calcWindow(ri['waveform'],
                ri['windowStart'])
            ri.update()
            coeff1 = ri['windowCoeff']
            fft1 = ri['windowFFT']

        for rj in tj:
            fft2 = rj['windowFFT']
            coeff2 = rj['windowCoeff']
            j = rj['id']
            Ctmp[j], Ltmp[j] = xcorr1x1(fft1, fft2, coeff1, coeff2)

    for j in range(0, i+1):
        if Ctmp[j] > 0.65:
            appendCorrelation(corr, i, j, Ctmp[j])

    ctable.flush()
            

print("Correlation done in: {:03.2f} seconds".format(time.time()-t))

C = np.zeros((len(rtable),len(rtable)))
C[ctable.cols.id1[:], ctable.cols.id2[:]] = ctable.cols.ccc[:]
C = C + C.T + np.eye(len(C))


# Copied from old stuff:
maxes = np.max(C - np.eye(len(C)), axis=0)
print("Orphans: {:.2%}".format(1.0* len(maxes[maxes<0.7]) / len(C)))

# Cluster with OPTICS
ttree = setOfObjects(1-C)
prep_optics(ttree,1)
build_optics(ttree,1)
order = ttree._ordered_list

Co = C[order, :]
Co = Co[:, order]

# Save the ordering to the correlation table attributes
h5file.root.hsr.correlation.attrs.order = order
h5file.root.hsr.correlation.attrs.reachability = ttree._reachability
h5file.root.hsr.correlation.attrs.coredist = ttree._core_dist

# Plot the C matrices (saturated below 0.65)
# Left is ordered by time
# Right is ordered by cluster ordering
fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(1, 2, 1)
ax.imshow(C, aspect='auto', vmin=0.6, vmax=1, interpolation='nearest')
ax = fig.add_subplot(1, 2, 2)
ax.imshow(Co, aspect='auto', vmin=0.6, vmax=1, interpolation='nearest')


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
