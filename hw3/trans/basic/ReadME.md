The test sample for basic operation.
**Usage**:
* Step 1: start all servers (any sequence)
* Step 2: load 1-4.txt to server 1-4 (all local transactions)
* Step 3: load 0.txt to server 0

**Expected Behavior**
* All local transactions are executed locally
* Server 0 doesn't have enough balance for the last transaction, so it starts paxos
* It collects local transactions from 1 & 2 (got a quorum), and commit the merged block

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
*Server 0*
Log: (0 2 10)
Balance: 8

*Server 1*
Log: empty
Balance: 10

*Server 2*
Log: empty
Balance: 2

*Server 3*
Log: (3 1 2)
Balance: 8

*Server 4*
Log: (4 2 3) (4 3 1)
Balance: 6
