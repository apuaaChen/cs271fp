import socketserver
import pickle
import sys
import time


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            mesg = self.request.recv(4096)
            mesg = pickle.loads(mesg)
            receive_handler(mesg, self.server)
        except EOFError:
            pass
        except KeyboardInterrupt:
            sys.exit()


def receive_handler(msg, server):
    # TODO: handlers for messages
    time.sleep(server.delay)
    # print('<Receive> Transaction received', end='\n')
    # try:
    # Upon receiving leader election <"prepare", ballotNum>
    if msg[0] == "prepare":
        ballot = msg[1]  # get ballot number from message
        print("<PREPARE> received prepare from Server %d" % ballot.id)
        # if the server is not in a ballot
        # or is currently in a ballot with smaller ballot number
        # join the new ballot
        if server.ballot_num is None or not server.ballot_num.greater(ballot):
            # return message
            # <"ack", the new ballot, previous accepted ballot number, previous accepted block, local bloc, idk>
            rmsg = ("ack", ballot, server.accept_ballot, server.accept_block, server.lblock, server.id)
            # move to the new ballot
            server.ballot_num = ballot
            # send ack to the candidate
            server.send(rmsg, ballot.id)
        else:
            # If the receiver is in the ballot with higher ballot number, reject
            rmsg = ("Reject", server.ballot_num, server.id)
            server.send(rmsg, ballot.id)

    # Upon receiving acknowledgement: acknowledge or reject
    elif msg[0] == "ack":
        # message is in format
        # <"ack", the new ballot, previous accepted ballot number, previous accepted block, local block>
        server.quorum.get_ack(msg[1], msg[2], msg[3], msg[4])
        print("<ACK> received acknowledgement from Server %d" % msg[5])
    elif msg[0] == "Reject":
        server.latest_ballot = msg[1].num
        print("<Reject> received reject from Server %d" % msg[2])

    # Upon receiving "accept?" from leader
    elif msg[0] == "accept?":
        ballot = msg[1]
        print("<ACCEPT?> received from Server %d" % ballot.id)
        # when the receiver is not in a ballot with greater number
        if server.ballot_num is None or (not server.ballot_num.greater(ballot)):
            server.accept_ballot = ballot  # the ballot number of accepted block
            server.accept_block = msg[2]  # the accepted block
            rmsg = ("accept", server.accept_ballot, server.accept_block, server.id)
        else:
            # If the receiver's ballot number is higher than what is received, reject
            rmsg = ("Reject", server.ballot_num, server.id)
        server.send(rmsg, ballot.id)
    # Upon receiving "commit" from leader
    elif msg[0] == "commit":
        print("<COMMIT> commit the blockchain")
        server.commit(msg[1])

    # Upon receiving accept
    elif msg[0] == "accept":
        print("<ACCEPT> received accept from Server %d" % msg[3])
        server.accept_counter += 1

    # Upon receiving "sync":
    elif msg[0] == "sync":
        print("<SYNC> received syn request from Server %d" % msg[2])
        if server.chain.tail.seq > msg[1]:
            rmsg = ("chain", server.chain.tail.seq, server.chain, server.id)
        else:
            rmsg = ("chain", server.chain.tail.seq, None, server.id)
        server.send(rmsg, msg[2])

    # Upon receiving "chain"
    elif msg[0] == "chain":
        print("<CHAIN> received chain from Server %d" % msg[3])
        server.sync_quorum.get_sync(msg[1], msg[2])
    # except:
    #     print("Unknown Message")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
