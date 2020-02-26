The test sample for concurrent leader operation.

The transactions on each servers should be executed as concurrent as possible, and in sequence

The expected behavior should be:

Local transactions:
server 0:
client 0 to client 1: $2
client 0 to client 1: $3

balance: 5

server 1:
client 1 to client 0: $2
client 1 to client 0: $3

balance 5

server 2:
client 2 to client 0: $5

balance 5

Then,

server 0 wants to execute client 0 to client 2: 11
server 2 wants to execute client 2 to client 0: 6

Both servers launch the paxos

As server 0 starts earlier, it will become the leader, and its merged block is
{
client 0 to client 1: $2
client 0 to client 1: $3
client 1 to client 0: $2
client 1 to client 0: $3
}

But server 2 has a higher ballot number, so it also becomes the leader with merged block
{
client 2 to client 0: $5
client 0 to client 1: $2
client 0 to client 1: $3
}

And server 1 joins server 2's ballot.

As a result, server 2 commits its block, and we have
server 0:

balance: 10

server 1:
client 1 to client 0: $2
client 1 to client 0: $3

balance 10

server 2:
balance 5

However, server 2 still doesn't have enough money, so it aborts the transaction

On the other side, server 1 learns that a new block is committed, it check its balance,
but the balance is still not enough for a transaction of 11.

So it launches a new paxos, now we have
Chain:
{
client 2 to client 0: $5
client 0 to client 1: $2
client 0 to client 1: $3
}
{
client 1 to client 0: $2
client 1 to client 0: $3
}

server 0:
client 0 to client 2 11
balance: 4

server 1:
balance 10

server 2:
balance 5

