"""
Class Transaction
A tuple (Sender, Receiver, amt)
"""
import numpy as np


class Transaction:
    def __init__(self, sender, receiver, amount):
        self.s = sender
        self.r = receiver
        self.amt = amount

    def print(self):
        print('client %d to client %d: $%d' % (self.s, self.r, self.amt))


def trans_reader(file):
    try:
        trans_array = np.loadtxt(file).astype(int)
        if trans_array.ndim == 1:
            trans_array = np.expand_dims(trans_array, axis=0)
        # get number of transactions in the file
        num_trans = trans_array.shape[0]
        trans_todo = []
        # read all the transactions into a todoList
        for i in range(num_trans):
            trans = trans_array[i]
            # the transactions are stored in [S, R, amt]
            trans_todo.append(Transaction(trans[0], trans[1], trans[2]))

        return trans_todo
    except IOError:
        return None
