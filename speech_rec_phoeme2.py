import numpy as np
import scipy
import os

import matplotlib.pyplot as plt
from numpy.lib.stride_tricks import as_strided

from sklearn.grid_search import GridSearchCV
from sklearn.ensemble import ExtraTreesClassifier

def stft(x, fftsize=64, overlap_pct=.5):   
    #Modified from http://stackoverflow.com/questions/2459295/stft-and-istft-in-python
    hop = int(fftsize * (1 - overlap_pct))
    w = scipy.hanning(fftsize + 1)[:-1]    
    raw = np.array([np.fft.rfft(w * x[i:i + fftsize]) for i in range(0, len(x) - fftsize, hop)])
    return raw[:, :(fftsize / 2)]

#Peak detection using the technique described here: http://kkjkok.blogspot.com/2013/12/dsp-snippets_9.html 
def peakfind(x, n_peaks, l_size=3, r_size=3, c_size=3, f=np.mean):
    win_size = l_size + r_size + c_size
    shape = x.shape[:-1] + (x.shape[-1] - win_size + 1, win_size)
    strides = x.strides + (x.strides[-1],)
    xs = as_strided(x, shape=shape, strides=strides)
    def is_peak(x):
        centered = (np.argmax(x) == l_size + int(c_size/2))
        l = x[:l_size]
        c = x[l_size:l_size + c_size]
        r = x[-r_size:]
        passes = np.max(c) > np.max([f(l), f(r)])
        if centered and passes:
            return np.max(c)
        else:
            return -1
    r = np.apply_along_axis(is_peak, 1, xs)
    top = np.argsort(r, None)[::-1]
    heights = r[top[:n_peaks]]
    #Add l_size and half - 1 of center size to get to actual peak location
    top[top > -1] = top[top > -1] + l_size + int(c_size / 2.)
    return heights, top[:n_peaks]


if __name__ == '__main__':
    fpaths = []
    labels = []
    spoken = []

    #all_labels = np.zeros(data.shape[0])
    all_labels = []

    data = np.array([])
    with open('npfda-phoneme.dat') as fp:
        for line in fp:
            dat = np.array([])
        
            ll = line.split(' ')
            for i in range(len(ll)):
                dat = np.append(dat, float(ll[i]))
            
                if i == len(ll)-1:
                    all_labels.append(int(ll[i]))
        
            if len(data) == 0:
                data = dat
            else:
                data = np.vstack((data, dat))

    all_labels = np.array(all_labels)
    
    print 'Labels and label indices',all_labels

    # This processing (top freq peaks) only works for single speaker case... need better features for multispeaker!
    # MFCC (or deep NN/automatic feature extraction) could be interesting

    n_dim = 6
    all_obs = np.zeros((data.shape[0], n_dim))
    for r in range(data.shape[0]):
        #obs = np.zeros((n_dim, 1))
        _, t = peakfind(data[r, :], n_peaks=n_dim)
        all_obs[r, :] = t.copy()
    
    #all_obs = np.atleast_3d(all_obs)
    print all_obs.shape
    print all_labels.shape

    forest = ExtraTreesClassifier(n_estimators=50)
    max_features_choices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    gs = GridSearchCV(forest, {'max_features': max_features_choices}, scoring = 'accuracy', cv = 10, n_jobs=-1)
    gs.fit(all_obs, all_labels)
    print gs.best_params_
    print gs.best_score_
