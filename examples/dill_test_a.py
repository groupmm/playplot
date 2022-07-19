from dill import dump
import numpy as np



def test(a):
    return np.zeros(a)


with open("dill_pickle.pck", 'wb') as f:
    dump(test, f, byref=False, recurse=True)

