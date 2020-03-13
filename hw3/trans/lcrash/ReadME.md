The test sample for leader crash and recover.

**Usage**:

* Step 1: start all servers (any sequence)
* Step 2: load 1-4.txt to server 1-4 (all local transactions)
* Step 3: load 0.txt to server 0
* Step 4: crash server 0 before commit. (just after other servers get <ACCEPT?>)
* Step 5: load 2_2.txt to server 2
* Step 6: restart server 0

**Expected Behavior**

* All local transactions are executed locally
* Server 0 doesn't have enough balance for the last transaction, so it starts paxos.
  It collects local transactions from 1 & 2 (got a quorum), and commit the merged block.
* The block committed by server 1 is accepted by the majority, but not committed
* When server 2 launches the paxos, it will commit the previous block first
* Then Server 2 will merge block from 1 & 3, and commit its own block, but it still doesn't have enough money.

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
(3 1 2)
\}

*Server 0*

Log: empty
Balance: 18

*Server 1*

Log: empty
Balance: 12

*Server 2*
Log: empty
Balance: 2

*Server 3*

Log: empty
Balance: 8

*Server 4*

Log: (4 2 3) (4 3 1)
Balance: 6
