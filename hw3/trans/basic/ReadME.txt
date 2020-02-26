The test sample for basic operation.
First, load 1 & 2 to server 1 & 2, respectively
Then, load 0 to server 0.

The expected result should like this.
Committed block:

Block 0:
client 0 to client 1: $2
client 0 to client 1: $3
client 1 to client 0: $2
client 1 to client 0: $3

Local logs:
server 0:
client 0 to client 2: $10
server 1:
empty
server 2:
client 2 to client 0: $5
client 2 to client 0: $3

Balance: 0 (local -10) , 10, 2 (local -2)