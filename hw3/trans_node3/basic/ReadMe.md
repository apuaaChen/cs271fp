This test sample is used for basic operation on three nodes.

**Usage**:

* Step 0: mkdir chains (if not existed and delete all the blockchains.txt of previous test cases)
* Step 1: start all servers (any sequence)
* Step 2: load 0.txt to Server 0 and 1.txt to Server 1
* Step 3: load 2.txt to Server 2

**Expected Behavior**

* All local transactions are executed locally
* Server 0 and Server 1 have enough balance for their local two transactions and succeed directly; while Server 2 does not have enough balance for the 2nd transaction, so it starts the leader election.
* It collects local transactions from 0 (got a quorum) and commit the merged block

**Chain, Log, Balance**

*Chain*
\{
(0 1 4)
(0 2 3)
(2 0 8)
\}

*Server 0*

Log: empty
Balance: 11

*Server 1*

Log: (1 2 3)(1 2 4)
Balance: 7

*Server 2*

Log: (2 0 4)
Balance: 1
