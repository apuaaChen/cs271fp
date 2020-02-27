"""
Code that generates a inferno test case
"""
import numpy as np


NUM_SERVER = 5
INIT_UNIT = 10
MAX_CASES = 20

for s in range(NUM_SERVER):
    num_case = np.random.randint(low=3, high=MAX_CASES, dtype=int)
    trans = np.zeros(shape=(num_case, 3))
    for c in range(num_case):
        trans[c][0] = s
        trans[c][1] = np.random.randint(low=0, high=4, dtype=int)
        trans[c][2] = np.random.randint(low=1, high=10, dtype=int)
    np.savetxt('trans/inferno/%d.txt' % s, trans, delimiter=' ')
