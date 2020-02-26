from utils import Transaction


# A single block
class Block:
    def __init__(self):
        self.trans_container = []
        self.next = None
        self.seq = 0  # seq marks the sequence number of current block

    def add_trans(self, trans):
        self.trans_container.append(trans)

    def merge(self, block):
        self.trans_container += block.trans_container

    # function that removes committed local transactions
    def wash(self, block):
        if len(self.trans_container) != 0:
            counter = 0
            balance_change = 0
            for tr in block.trans_container:
                if tr.s == self.trans_container[0].s:
                    counter += 1
                    balance_change += tr.amt
            self.trans_container = self.trans_container[counter:]
            return balance_change
        else:
            return 0

    def balance_change(self, id):
        delta = 0
        for tr in self.trans_container:
            if tr.r == id:
                delta += tr.amt
            elif tr.r != id and tr.s == id:
                delta -= tr.amt
        return delta

    def print(self):
        for tr in self.trans_container:
            tr.print()


# blockchain
class Blockchain:
    def __init__(self, id):
        self.head = Block()
        self.head.seq = -1
        self.head.add_trans(Transaction(id, id, 10))
        self.tail = self.head
        self.id = id
        self.buffer = []

    def add_block(self, block):
        if block.seq == self.tail.seq + 1:
            self.tail.next = block
            block.seq = self.tail.seq + 1
            self.tail = block
        elif block.seq >= self.tail.seq + 1:
            self.buffer.append(block)
        else:
            print("Something wrong!, trying to commit an exist block")

    def clear_buffer(self):
        if len(self.buffer) != 0:
            for block in self.buffer:
                self.add_block(block)

    def merge(self, chain):
        block = chain.head  # current block
        while block.next is not None:
            block = block.next
            if block.seq > self.tail.seq:
                self.add_block(block)
        self.clear_buffer()

    def get_balance(self):
        block = self.head  # current block
        balance = block.balance_change(self.id)
        while block.next is not None:
            block = block.next
            balance += block.balance_change(self.id)
        return balance

    def print(self):
        block = self.head  # current block
        counter = -1
        while block.next is not None:
            counter += 1
            print("Block %d:" % counter)
            block = block.next
            block.print()
