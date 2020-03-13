The test sample for leader crash and recover in the case of three nodes.

**Usage**

* Step 1: start all servers (any sequence)
* Step 2: load 1.txt to Server1; load 2.txt to Server2 (all local transactions)
* Step 3: load 0.txt to Server 0 (the last transaction init paxos)
* Step 4: crash Server 0 before commit (just after Server1 and Server 2 get <ACCEPT?>)
* Step 5: load 2_1.txt to Server 2
* Step 6: Recover Server 0
* Step 7: load 0_2.txt to Server 0

**Expected Behavior**

* All local transactions are executed locally
* At Step 2, Server 1 and Server 2 finish all the txs
* Yet at Step 3, Server 0 does not have enough balance for the last transaction, so it starts paxos.

	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0	|5		|(0,1,2)(0,1,3)	|(0,2,10)	|
	|Server1	|5		|(1,0,2)(1,0,3)	|			|
	|Server2	|2		|(2,0,5)(2,0,3)	|			|

* During the paxos process, Server 0 crashed before commit (after Server 1 and Server 2 get <ACCEPT?>) Then there will be an uncommitted block (with Server0's and Server1's previous local logs); the Server0's pending tx gets lost.


	Uncommited Block 0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0(C)	|-		|-				|-			|
	|Server1	|10		|				|			|
	|Server2	|2		|(2,0,5)(2,0,3)	|(2,0,3)	|

* Then we load 2_1.txt to Server2, it does not have enough money to make the pending tx, and starts paxos for leader election. It becomes leader and commits the previous uncommitted Block0, and the new Block1 (its local log). However, Server2 still does not have enough money, so the pending (2, 0, 3) is abort.

	Block 0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block 1: {(2,0,5)(2,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0(R)	|18		|				|			|
	|Server1	|10		|				|			|
	|Server2	|2		|				|			|

* Then Server0 recovers. After it sync with others, we load the 0_2.txt to Server 0.
	Block 0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block 1: {(2,0,5)(2,0,3)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0(R)	|10		|(0,2,8)		|(0,1,12)	|
	|Server1	|10		|				|			|
	|Server2	|2		|				|			|

* Server 0's balance is not enough for the pending tx (0, 1, 12), then it starts the paxos for leader election. 
* Note: Server 0 wiil have two rounds of leader elections.The first round will fail because in our implement the ballot number is reinitialized as 0 after recovering; (be patient, it will wait till timeout); and it will be updated to the more advanced one when getting reject by others.
* Finally, Server 0 is re-elected as the leader, it will commit its local log {(0,2,8)} as Block2. Yet Server 0 still does not have enough money to process (0,1,12) and abort it directly.
	Block 0: {(0,1,2)(0,1,3)(1,0,2)(1,0,3)}
	Block 1: {(2,0,5)(2,0,3)}
	Block 2: {(0,2,8)}
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0(R)	|10		|				|			|
	|Server1	|10		|				|			|
	|Server2	|10		|				|			|
