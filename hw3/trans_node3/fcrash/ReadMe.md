The test sample for follower crash and recover in the case of three nodes.

** Usage **

* Step 1: start all three servers (any sequence)
* Step 2: load 1.txt and 2.txt to Server 1 and Server 2 respectively.
* Step 3: load 0.txt to Server 0
* Step 4: Crash Server 1 when Server 0 becomes the leader
* Step 5: load 0_1.txt
* Step 6: restart server 1 afterwards
* Step 7: load 0_2.txt

**Expected Behavior**

* All local transactions are executed locally
* Server 1 and Server 2 finishes all the transaction
* Yet Server 0 doesn't have enough balance for the last transaction, so it starts paxos
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0	|5		|(0,1,2)(0,1,3)	|(0,2,10)	|
	|Server1	|5		|(1,0,2)(1,0,3)	|			|
	|Server2	|2		|(2,0,5)(2,0,3)	|			|

* After it becomes leader, it merges the block {(0,1,2)(0,1,3)(1,0,2)(1,0,3)} and commit.
* Note: Server1 must crash after "accept-ack" stage; otherwise, Server0 will form the majority quorum with Server2 and Server1's local log {(1,0,2)(1,0,3)} will be lost and unrecoverable in the crash.
* Similarly, if Server2 crash at this moment and it is not in the majority quorum, then Server2's local log will be lost and unrecoverable in the crash.

	Block0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0 (L)|0		|(0,2,10)		|(0,1,3)	|
	|Server1 (C)|-		|-				|-			|
	|Server2	|2		|(2,0,5)(2,0,3)	|			|

* Then Server0 wants to send Server1 $3, and starts paxos again. This time, since Server1 has crashed, it will form the majority quorum with Server2. Merge another block and commit.
	Block0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block1: {(0,2,10)(2,0,5)(2,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0 (L)|5		|(0,1,3)		|			|
	|Server1 (C)|-		|-				|-			|
	|Server2	|12		|				|			|

* Now Recover Server 1, it will get the block chain from peers.
	Block0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block1: {(0,2,10)(2,0,5)(2,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0 (L)|5		|(0,1,3)		|(0,2,2)	|
	|Server1 	|10		|				|			|
	|Server2	|12		|				|			|

* Finally Server 0 wants to send Server2 $2, and directly record it in the local log, though Server1 and Server 2 know nothing about it.
	Block0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block1: {(0,2,10)(2,0,5)(2,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0 (L)|3		|(0,1,3)(0,2,2)	|			|
	|Server1 	|10		|				|			|
	|Server2	|12		|				|			|