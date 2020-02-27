The test sample for concurrent leader election. We have 5 concurrent leaders

**Usage**:

* Step 1: start all servers (any sequence)
* Step 2: input 0-4.txt to server 0-4, but not confirm
* Step 3: confirm from 0 - 4 as quick as possible

**Expected Behavior**

* All local transactions are executed locally
* All servers don't have enough money for their last transaction, so all of the servers will start paxos
* Server 4 has the largest ballot number. It merges blocks and have \{(4 1 9) (0 1 2) (0 1 3) (1 0 2) (1 0 3)\}
* After this commit, Server 0 has balance 10, but wanna transfer 11, performs paxos
* Server 1 has balance 19, wanna transfer 7, so the transaction is executed. remaining balance 12. Log (1 4 7)
* Server 2 has balance 5, wanna transfer 6, performs paxos
* Server 3 has balance 8, wanna transfer 9, perform paxos
* Server 3 has the second largest ballot number, it merges \{(3 4 2) (1 4 7)\}, and commit it, it still doesn't have 9, so abort
* After this commit, Server 0 has balance 10, but wanna transfer 11, performs paxos
* Server 1 has balance 12
* Server 2 has balance 5, wanna transfer 6, perform paxos
* Server 2 has the largest ballot number, it merges \{(2 0 5)\}, still doesn't have 6, abort
* Server 0 has balance 15, transfer 11, balance 4.


**Chain, Log, Balance**

*Chain*
\{
(4 1 9)
(0 1 2)
(0 1 3)
(1 0 2)
(1 0 3)
\}
\{
(3 4 2)
(1 4 7)
\}
\{
(2 0 5)
\}

*Server 0*

Log: (0 2 11)
Balance: 4

*Server 1*

Log: empty
Balance: 12

*Server 2*

Log: empty
Balance: 5

*Server 3*

Log: (3 1 2)
Balance: 8

*Server 4*

Log: (4 2 3) (4 3 1)
Balance: 10