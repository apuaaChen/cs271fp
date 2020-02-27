The test sample for follower crash and recover.

**Usage**:

* Step 1: start all servers (any sequence)
* Step 2: load 1-4.txt to server 1-4 (all local transactions)
* Step 3: load 0.txt to server 0
* Step 4: crash server 1 & 2 when server 0 becomes the leader
* Step 5: restart server 2 afterwards
* Step 6: load 0_2.txt
* Step 7: restart server 1 before commit

**Expected Behavior**

* All local transactions are executed locally
* Server 0 doesn't have enough balance for the last transaction, so it starts paxos.
  It collects local transactions from 1 & 2 (got a quorum), and commit the merged block.
* Crashed server 1 & 2 didn't get the first update
* When server 2 restarts, it get the chain from other servers
* Then server 0 executes paxos on the new transaction file, but eventually it doesn't have enough balance
* When server 1 restarts, it sync the chain. If it gets commit before sync,
  the commit itself will also start the sync progress.

**Chain, Log, Balance**

*Chain*
\{
(0 1 2)
(0 1 3)
(1 0 2)
(1 0 3)
(2 0 5)
(2 0 3)
\}
\{
(0 2 10)
(0 3 7)
(3 1 2)
\}

*Server 0*

Log: empty
Balance: 1

*Server 1*

Log: empty
Balance: 12

*Server 2*

Log: empty
Balance: 12

*Server 3*

Log: empty
Balance: 15

*Server 4*

Log: (4 2 3) (4 3 1)
Balance: 6
