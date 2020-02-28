import argparse
import socket
import sys
import threading
import pickle
import os
import time
from utils import Blockchain, ThreadedTCPServer, ThreadedTCPHandler, trans_reader, Block

parser = argparse.ArgumentParser("Initiate a client")
parser.add_argument('--id', choices=[0, 1, 2, 3, 4], type=int, default=0, help='choose client')
parser.add_argument('--num_server', type=int, default=5, help='total number of servers')
args = parser.parse_args()

# the ip & port of each server
SERVERS = {
    0: {'ip': '127.0.0.1', 'port': 2000, },
    1: {'ip': '127.0.0.1', 'port': 2001, },
    2: {'ip': '127.0.0.1', 'port': 2002, },
    3: {'ip': '127.0.0.1', 'port': 2003, },
    4: {'ip': '127.0.0.1', 'port': 2004, },
}


class Ballot:
    def __init__(self, num, id):
        self.num = num
        self.id = id

    def greater(self, ballot):
        if self.num > ballot.num or (self.num == ballot.num and self.id > ballot.id):
            return True
        else:
            return False

    def increment(self):
        self.num += 1

    def update(self, ballot):
        self.num = ballot.num

    def match(self, ballot):
        if self.num == ballot.num and self.id == ballot.id:
            return True
        else:
            return False


class Quorum:
    def __init__(self, num_server, laccept_ballot, laccept_block, ballot):
        self.accept_ballot = laccept_ballot
        self.accept_block = laccept_block
        self.num_ack = 1  # the one is from it self
        self.quorum_size = (num_server - 1) / 2 + 1
        self.local_blocks = []
        self.ballot = ballot

    # Upon getting an acknowledgement
    def get_ack(self, ballot, accepted_ballot, accepted_block, rlblock):
        # Each time, we only merge transactions from quorum_size amount of servers
        if self.ballot.match(ballot):
            if self.num_ack < self.quorum_size:
                self.num_ack += 1
                self.local_blocks.append(rlblock)
                if accepted_ballot is not None:
                    # take the accepted value with the highest ballot
                    if self.accept_ballot is None or accepted_ballot.greater(self.accept_ballot):
                        self.accept_ballot = accepted_ballot
                        self.accept_block = accepted_block

    def reset(self, laccept_ballot, laccept_block, ballot):
        self.accept_ballot = laccept_ballot
        self.accept_block = laccept_block
        self.num_ack = 1
        self.local_blocks = []
        self.ballot = ballot


class SyncQuorum:
    def __init__(self, num_server, seq):
        self.seq = seq
        self.chain = None
        self.num_syn = 1  # including itself
        self.quorum_size = (num_server - 1) / 2 + 1

    def get_sync(self, seq, chain):
        self.num_syn += 1
        if seq > self.seq:  # when some server has higher sequence number
            self.seq = seq
            self.chain = chain

    def reset(self, seq):
        self.seq = seq
        self.chain = None
        self.num_syn = 1  # including itself


class Server(ThreadedTCPServer):
    def __init__(self, id, server_address, RequestHandlerClass):
        # Basic components of the server #
        super().__init__(server_address, RequestHandlerClass)
        self.id = id  # the server's id
        # incoming message listener
        # self.server_ = ThreadedTCPServer((SERVERS[id]['ip'], SERVERS[id]['port']), ThreadedTCPHandler)
        self.tcp_listener = threading.Thread(target=self.serve_forever)
        self.tcp_listener.daemon = True
        # the path to the block chain
        self.chain_path = './chains/blockchain%d.txt' % id
        # local block chain
        self.chain = Blockchain(self.id)
        # initial balance
        self.balance = 0
        # local block
        self.lblock = Block()

        self.delay = 5. + self.id * 0.1

        # Paxos related #
        # the latest known ballot, used to generate now ballot number
        self.latest_ballot = 0
        # the ballot number of the ballot that the server currently belongs to
        self.ballot_num = None
        # the block it accepted
        self.accept_block = None
        # the ballot number of the accepted block
        self.accept_ballot = None
        # the quorum for election (also collects the accepted blocks)
        self.quorum = Quorum(args.num_server, self.accept_ballot, self.accept_block, self.ballot_num)
        # the quorum counter for accept
        self.accept_counter = 1

        # Step 1: load chain from file
        self.load_chain()

        # Step 2: start TCP listener
        self.start_listener()

        # the quorum counter for blockchain sync
        self.sync_quorum = SyncQuorum(args.num_server, self.chain.tail.seq)
        self.sync_block()

        # get balance
        self.update_balance()

    # load the previously saved blockchain from file
    def load_chain(self):
        if os.path.exists(self.chain_path):
            self.chain = pickle.load(open(self.chain_path, "rb"))
            self.lblock.seq = self.chain.tail.seq + 1
        else:
            print("No blockchain is found")

    def update_balance(self):
        self.balance = self.chain.get_balance() + self.lblock.balance_change(self.id)

    # write the chain to file
    def save_chain(self):
        pickle.dump(self.chain, open(self.chain_path, "wb"))

    # Part I: Leader Election
    def leader_election(self):
        # step 1: generate the ballot <ballotNum, Id>
        self.ballot_num = Ballot(self.latest_ballot, self.id)
        # increment ballot number by 1
        self.latest_ballot += 1
        self.ballot_num.increment()
        self.latest_ballot += 1
        # broad cast leader prepare message to all
        mesg = ("prepare", self.ballot_num)
        self.broadcast(mesg)
        self.quorum.reset(self.accept_ballot, self.accept_block, self.ballot_num)
        self.lblock.seq = self.chain.tail.seq + 1
        counter = 0
        # step 3: collect acknowledgement
        while self.quorum.num_ack < (args.num_server - 1) / 2 + 1:
            counter += 1
            time.sleep(0.1)
            # If the seq number of the block to commit is smaller/equal to the chain's tail
            # (other process commit a block)
            if self.lblock.seq <= self.chain.tail.seq:
                return True
            if counter > 1200:
                return True
        # once getting enough messages, the server becomes the leader
        print("[LEADER] Get enough ack to become the leader")  # the server has become the leader
        return False

    def commit(self, block2commit):
        # commit the new block to chain
        incomplete = self.chain.add_block(block2commit)
        if incomplete:
            self.sync_block()
        # reset the accepted block and ballot
        if self.accept_block is not None:
            if self.accept_block.seq <= block2commit.seq:
                self.accept_block = None
                self.accept_ballot = None
        # save the chain to local file
        self.save_chain()
        # update the balance and remove committed logs in local log
        self.lblock.wash(block2commit)
        self.update_balance()
        # self.lblock.seq = self.chain.tail.seq + 1

    # Part II: Normal Operations
    def normal(self, block2commit, ballot):
        self.accept_block = block2commit
        self.accept_ballot = ballot
        # broadcast message <accept?, ballotNum, block to commit>
        msg = ("accept?", self.ballot_num, block2commit)
        self.broadcast(msg)
        # collect accept from quorum
        self.accept_counter = 1
        counter = 0
        while self.accept_counter < (args.num_server - 1) / 2 + 1:
            counter += 1
            time.sleep(0.1)
            if block2commit.seq <= self.chain.tail.seq:
                self.lblock.seq += 1
                return True
            if counter > 1200:
                return True
        print("[COMMIT] the block is accepted by the majority")
        msg = ("commit", block2commit)
        self.broadcast(msg)
        self.commit(block2commit)
        return False

    def trans_perform(self, todo_list):
        for tr in todo_list:
            if tr.s != self.id:
                print("[Error] Can only send money from your own account")
            else:
                if tr.r == self.id:
                    print("[Ignored] You are sending money to yourself")
                else:
                    self.paxos(tr)

    def paxos(self, tr):
        time.sleep(0.5)
        # If the balance on the client account is at least amt
        # the server logs the request, and executes the transfer locally
        if tr.amt <= self.balance:
            self.lblock.add_trans(tr)
            self.update_balance()
            print("[SUCCESS] Transaction (local) SUCCESS, current balance %d" % self.balance)
        # Otherwise, the server runs a modified Paxos protocal among all servers
        # to get the most up-to-date transactions from other servers and then
        # updates its blockchain copy
        else:
            # Part I: Leader Election
            fail = self.leader_election()
            if fail:
                print("[FAIL] Failed in leader election, try again")
                self.paxos(tr)
            else:
                # Part II: Normal Operation
                # if some followers have previously accepted blocks
                # process the previously accepted block first
                if self.quorum.accept_block is not None:
                    print("[PRE] commit previously accepted block first")
                    self.quorum.accept_block.seq = self.lblock.seq
                    self.lblock.seq += 1
                    fail = self.normal(self.quorum.accept_block, self.quorum.accept_ballot)
                    if fail:
                        # if found out it is not the leader any more
                        # redo paxos to see if there is enough money
                        # after the update
                        print("[FAIL] Failed to commit previous block, try again")
                    # anyway, a new block is committed
                    # so check the new balance before continuing
                    self.paxos(tr)
                else:
                    # If there is no accepted block returned
                    # merge the block to commit
                    merge_block = Block()
                    merge_block.merge(self.lblock)
                    for b in self.quorum.local_blocks:
                        merge_block.merge(b)
                    merge_block.seq = self.lblock.seq
                    # accept? and commit the merged block
                    fail = self.normal(merge_block, self.ballot_num)
                    if fail:
                        # if the server is not leader anymore
                        # cause a new block is committed
                        # check the balance and redo paxos
                        print("[FAIL] Failed to commit merged block, try again")
                        self.paxos(tr)
                    else:
                        # else, the merged block is committed
                        # check whether the balance is enough for the transaction
                        if tr.amt <= self.balance:
                            self.lblock.add_trans(tr)
                            self.update_balance()
                            print("[SUCCESS] Transaction (local) SUCCESS, current balance %d" % self.balance)
                        else:
                            print("[ERROR] Not enough money, current balance %d" % self.balance)

    def sync_block(self):
        print("Start syncing block chain")
        # when the server starts (recovers), it contacts other servers for the latest blockchain
        # step 1: broad cast the request with <"sync", local largest seq number, id>
        msg = ("sync", self.chain.tail.seq, self.id)
        self.broadcast(msg)
        timeout = False
        counter = 0
        while self.sync_quorum.num_syn < self.sync_quorum.quorum_size:
            time.sleep(0.1)
            counter += 1
            if counter > 200:
                timeout = True
                self.sync_block()
        if not timeout:
            # get enough chains
            if self.sync_quorum.chain is None:
                print("[SYNC] No need to update")
            else:
                self.chain.merge(self.sync_quorum.chain)
                print("[SYNC] Local Chain is updated")

    # start the TCP listener
    def start_listener(self):
        try:
            self.tcp_listener.start()
        except KeyboardInterrupt:
            self.shutdown()
            sys.exit()

    @staticmethod
    def send(mesg, target):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVERS[target]['ip'], SERVERS[target]['port']))
            mesg = pickle.dumps(mesg)
            sock.sendall(mesg)
            sock.close()
        except ConnectionError:
            pass

    def broadcast(self, mesg):
        for i in range(args.num_server):
            if i != self.id:
                Server.send(mesg, i)


def control_cmd(server):
    try:
        action = input("Please choose the action to perform (Trans/Balance/Log/Chain/Kill): ")
        if action == "Trans":
            trans_file = input("The path to the transaction file: ")
            todo_list = trans_reader(trans_file)
            if todo_list is None:
                print("[Error] No transaction file is found")
            else:
                server.trans_perform(todo_list)
        elif action == 'Kill':
            server.shutdown()
            sys.exit(0)
        elif action == 'Balance':
            print("[Balance] Current Balance (local) is %d" % server.balance)
        elif action == "Chain":
            server.chain.print()
        elif action == "Log":
            server.lblock.print()
        else:
            print("Don't tell you :P")
        control_cmd(server)
    except KeyboardInterrupt:
        server.shutdown()


server = Server(args.id, (SERVERS[args.id]['ip'], SERVERS[args.id]['port']), ThreadedTCPHandler)
control_cmd(server)
