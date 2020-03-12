The test sample for concurrent leader election in the case of 3 nodes.

**Usage**

* Step 1: start all three servers
* Step 2: feed input0.txt, input1.txt, input2.txt to the corresponding servers but DON'T "ENTER" instantly after typing the path; try to confirm them as simultaneously as possible

**Expected Behavior**

* All local transactions are executed locally
	|	        |Balance|Local Log		|Pending Txs|
	|-----------|-------|---------------|-----------|
	|Server0	|5		|(0,1,2)(0,1,3)	|(0,2,11)	|
	|Server1	|5		|(1,0,2)(1,0,3)	|(1,2,7)	|
	|Server2	|5		|(2,0,5)		|(2,0,6)	|

* All three servers don't have enough money for their last transaction, so all of the server will start paxos

* Server2 has the largest ballot number and it merges block and commits to blockchain.
* Note: Server1 has the second largest ballot, so it may print out the leader-success log during the prepare-promise stage when Server0 first accepts Server1 and then later changes to accept Server2, but during the accept-ack stage, Server1 will be rejected by Server0 and find itself not the leader by the updated largest ballot.

	Block0: {(0,1,2)(0,1,3)(2,0,5)}

	|        	|Balance|Local Log				|Pending Txs|
	|-----------|-------|-----------------------|-----------|
	|Server0	|10		|						|(0,2,11)	|
	|Server1	|3		|(1,0,2)(1,0,3)(1,2,7)	|			|
	|Server2(L)	|5		|						|(2,0,6)	|

* Now Server1 has enough money (balance=10), to do the pending Txs (balance=3);
* Yet Server0 does not have enough money to do the pending Txs, do paxos.
* Yet the leader Server2 still does not have enough memory to do the pending Tx, abort.

* Now Server0 becomes the leader. With the merged block from Server1, it commits another block to the blockchain. Then it has enough money for the pending Tx.

	Block0: {(0,1,2)(0,1,3)(2,0,5)}{(1,0,2)(1,0,3)(1,2,7)}

	|        	|Balance|Local Log				|Pending Txs|
	|-----------|-------|-----------------------|-----------|
	|Server0(L)	|4		|(0,2,11)				|			|
	|Server1	|3		|						|			|
	|Server2	|12		|						|			|
