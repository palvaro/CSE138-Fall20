# Overview

## Course

CSE 138: Distributed Systems

## Date

- Due     : 12/14/2020

In this assignment, your team will implement a distributed key-value store that is partition-tolerant, available, and causally consistent. In other words, in the event of a partition, your team’s key-value store is expected to be **available**, while still providing some consistency–specifically **causal consistency**.

Sharding key-value pairs achieves *scalablility*, but the key-value store must **replicate** (make identical copies) each shard to provide redundancy, and thus be **fault-tolerant**. Without redundancy, a key-value store is fated to experience a network partition or a crash right when you want to demo your photo gallery of baby hippos. The number of replicas of a shard is called the *replication factor*. For completeness, a key-value store with a replication factor of one means that each shard is stored on a single node, so redundancy only exists if the replication factor is greater than one.

Consider a key-value store that has four nodes in its view, and a replication factor of two. In this scenario, the key-value store must partition the keys into shards, where each shard is then replicated across two nodes, as in the ascii diagram below. We will always specify the number of nodes in the view to be a multiple of the replication factor: **replication_factor = 3**, would require the view to have six nodes (2 shards = 6 nodes / 3 replicas), nine nodes (3 shards = 9 nodes / 3 replicas), etc.

```
+-----------------------+   +-----------------------+   +------------+   +------------+
|   node1               |   |   node2               |   |   node3    |   |   node4    |
| --------------------- |   | --------------------- |   | ---------- |   | ---------- |
|  shard1               |   |  shard1               |   |  shard2    |   |  shard2    |
|  replica1             |   |  replica2             |   |  replica1  |   |  replica2  |
| --------------------- |   | --------------------- |   | ---------- |   | ---------- |
|  - key1               |   |  - key1               |   |  - key2    |   |  - key2    |
|  - key3               |   |  - key3               |   |  - key4    |   |  - key4    |
|  - key5               |   |  - key5               |   |  - key6    |   |  - key6    |
|  - attending_class    |   |  - attending_class    |   |  - key8    |   |  - key8    |
+-----------------------+   +-----------------------+   +------------+   +------------+
```

However, when there is data redundancy, extra effort is required to maintain the same value for every copy of each shard. In other words, we need a protocol to guarantee that every replica is consistent – a consistency protocol. There are two kinds of bad scenarios we want our protocol to prevent:

- applying writes (inserts or updates) in a bad order and overwriting a newer value with an older value;

- responding to reads (gets) with a later event (the “effect”) without knowledge of an earlier event (the “cause”). For this assignment, your team’s protocol must enforce correctness via causal consistency, a property defined based on the happens before relation (→), which describes the “potentially causal” ordering between two events, A and B, in a system: A → B.

The happens before relation describes an order between events in the following ways:

- A message’s **send** event always *happens before* its **receive** event;

- two events that originate from the same process (a **receive**, a **send**, updating a value, etc.) can be ordered by that process into an earlier and later event;

- if an event B happens after A and before C, then A also happens before C. Any events that cannot be relatively ordered in this way appear to be independent, meaning that they can be applied in any order (writes) or served in any order (reads).

To illustrate applying writes in a causal order (preventing bad scenario #1), consider these events:

- Event **A1**: Node1 receives an insert of attending_class to 4 from Client1

- Event **B1**: Node1 receives a read of attending_class (aka event **B1**) from Client2

- Event **A2**: Node2 receives an update of attending_class to 5 from Client2

We are able to establish **A1 → B1** because they originate from the same process, Node1. We are then able to establish **B1 → A2** because a client, **Client2**, receives the response for **B1** before sending the request **A2** to Node2. These events are depicted in the diagram below, where we also show that Node1 sends knowledge of (**gossips**) **A1** to Node2 after Node2 has seen **A2**. Applying the writes (**attending_class = 5** and **attending_class = 4**) in causal order requires Node2 and Node1 to determine: **A1 → B1 → A2**. This would allow Node2 to finalize the value of **attending_class** as 5 (event **A2**) instead of 4 (event **A1**).

```
           "req" means request                                   "res" means response
+---------+                   +---------+               +---------+                +-------+
| Client1 |                   |  Node1  |               | Client2 |                | Node2 |
+---------+                   +---------+               +---------+                +-------+
    | (1) PUT attending_class = 4 |                         |                         | 
    | --------  A1 req  --------> |                         |                         |
    |                             |                         |                         | 
    |           (2) ack           |                         |                         | 
    | <--------  A1 res  -------- | (3) GET attending_class |                         |
    |                             | <------  B1 req  ------ |                         |
    |                             |                         |                         |
    |                             | (4) attending_class = 4 |                         |
    |                             | ------  B1 res  ------> |                         |
    |                             |                         | (5) attending_class = 5 |
    |                             |                         | ------  A2 req  ------> |
    |                             |                         |                         |
    |                             |                         |         (6) ack         |
    |                             |                         | <-----  A2 res  ------- |
    |                             |                         |                         |
    |                             |          (7) replicate attending_class            |
    |                             | -------------  Gossip about A1,B1  -------------> |
    |                             |                         |                         |
    |                             |          (8) replicate attending_class            |
    |                             | <--------------  Gossip about A2  --------------- |
    |                             |                         |                         |
    v                             v                         v                         v
```

Notice, though, that the relation between **B1** and **A2** is non-trivial and is only known via the process, Client2. The key-value store, then, requires some extra help from Client2 to make the correct association in the form of a **causal-context**. Client2 must piggyback the causal context with requests for B1 and A2 to convey the necessary information for the key-value store to relate these events as B1 → A2.

More specifically, **causal-context** should represent the history of the data operations, which means when sending the request, the client has already witnessed all the events carried by **causal-context**. The new **causal-context** should carry the events from the old one as well as the event(s) witnessed by the current data operation.

In the Alice and Bob example, suppose a database contains two replicas: R1 and R2. Alice sends **Write(A="Bob smells")** (aka **E1**) to R1. The response to Bob **Read(A)** from Replica1 should carry **causal-context** like: *Bob knows that Alice writes "Bob smells"*. Bob sends **Write(B="F you Alice")** together with **causal-context** to R2. Then Carol comes along and reads **B="F you Alice"** from R2. Carol wants to know what happened to Alice by sending **Read(A)** to R2. R2 may return:

- R2 has received the gossip about **E1**. Carol will read *Bob smells*.

- Alice writes something else like **Write(A="Bob still smells")** (aka **E2**), we will get the happens before relationship **E1 → E2** saying *Alice writes "Bob still smells" after writing "Bob smells"*. **E2** can be sent to R2 directly from Alice (Alice -> R2) or through gossip (Alice -> R1, R1 -> R2). Carol will read *Bob still smells*.

- In some cases (e.g. network partitions), R2 is unable to receive the gossip about **E1**. Carol's read will fail since from R2's prospective, the value of **A** that Carol asks for **must be** based on the witness of **E1**. R2 should return "Unable to satisfy request", which will be discussed later.

Your team is free to implement the causal context in a variety of ways, since it will also depend on how the consistency protocol is implemented. All clients are required to receive a causal context in a response from the key-value store and include it in the next request to the key-value store.

## Requirements

In this assignment, your key-value store will partition keys into shards, replicate each shard on more than one node, and guarantee causal consistency.

- You must do your work as part of a team. Your team may not use an existing key-value store (e.g. Redis, MongoDB, etc.)

- You will use **Docker** to create an image that runs a key-value store node and listens to port 13800.

- Your team’s available, causally consistent key-value store must:

    - Run as a collection of communicating instances, or nodes, where each node is capable of handling a request and responding to the client.

    - Partition key-value pairs into disjoint subsets, or shards.

        - Each key belongs to exactly one shard

        - Each shard is stored by “repl-factor” nodes (if repl-factor = 3, then each shard is stored by 3 nodes).

        - You are free to choose any mechanism to partition key-value pairs across shards

        - You are free to choose any mechanism to replicate key-value pairs across nodes
    - Maintain relatively balanced sizes of each shard (the count of key-value pairs in the shard) when the key-value store is started and after a view change.

    - Support view change requests, where new nodes are added to, or existing nodes are removed from, the key-value store.

        - A view change is only done when requested, and not in response to network partitions.

        - A view change will require a reshard and may change the replication factor.

    - Guarantee causal consistency.

        - A causal context will be necessary to share causal histories between processes. Clients will participate in the propagation of causal context objects.

        - You are free to choose any protocol for causal consistency.
    
    - Guarantee eventual consistency.

        - When there is no network partition, all replicas converge to newest, correct state. A gossip protocol must be implemented for replicas to exchange state.
        
        - You are free to implement your gossip protocol in any way.

- Each node of your team’s distributed key-value store:

    - Does not need to persist data; storing keys only in memory is okay.

    - Must be able to insert, update, get, and delete key-value pairs.

    - Must be able to get the number of key-value pairs that is stored.

    - Must be able to get metadata information about each shard.

    - Will be provided with:

        - Its own IP address and port number

        - The addresses of all other nodes of the key-value store

        - The replication factor

## Building and testing your container

- We will provide test script(s) that you **should** use to test your work.

- The provided tests are similar to the tests we will use to evaluate your submitted assignment.

- For all JSON responses, outputs will be compared based on structure. This means that whitespace, order of dictionary keys, and order of list items do not matter. However, be sure that string contents do match exactly.

- View-change requests will not be sent to new nodes outside the existing view. That is, if a view-change request is made it will be from a client to a node that is currently in the view.

## Submission workflow

- Create a new private repository, or reuse the previous private repository, for the team.

- Add the appropriate Github accounts (team members and ucsc-cse138-staff) to your private repository, if necessary.

- The repository should contain:

    - The Dockerfile defining how to build your Docker image.

    - The project file(s) implementing the key-value store.
    
    - A file, member-contributions.tsv, describing contributions of each team member.
    
    - Submit CruzID of your contact person, repository URL, and the commit ID (aka commit hash) to be evaluated here: https://forms.gle/MtcMSxepB4fuQK6w7

    - The commit timestamp must be no later than 12/14/2020 11:59 PM PDT

    - The google form must be submitted within a reasonable time of the due date (preferably 10 minutes).
    
    - Late submissions are accepted, with a 10% penalty for every 24 hours after the above deadline.

    - Only one of the team members needs to submit the form.

## Docker Network Management

- Container Options and Environment:

    - ADDRESS – a required environment variable that provides the address of the node being started

    - VIEW – a required environment variable that provides the address of each node in the store

    - REPL_FACTOR – a required environment variable that provides the replication factor, or number of replicas, for each shard.

    - ip – a required container property that assigns the given IP address to the container

    - p – a required container property that binds the given host port to the given container port

    - net – a required container property that connects the container to the given network

    - name – a convenience property so that we can distinguish between containers using a human readable name

- In the following, we explain a scenario where we have four nodes, and a Docker subnet named kv_subnet.

    - Create subnet, **kv_subnet**, with IP range **10.10.0.0/16**:

    ```bash
    $ docker network create --subnet=10.10.0.0/16 kv_subnet
    ```

    - Build Docker image containing the key-value store implementation:

    ```bash
    $ docker build -t kvs:4.0 <path-to-Dockerfile-directory>
    ```
    
- Run four instances at IP's 10.10.0.2, 10.10.0.3, 10.10.0.4 and 10.10.0.5, and listening to port 13800:  

    ```bash
    $ docker run -p 13800:13800                                                            \
                 --net=kv_subnet --ip=10.10.0.2 --name="node1"                             \
                 -e ADDRESS="10.10.0.2:13800"                                              \
                 -e VIEW="10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800" \
                 -e REPL_FACTOR=2                                                          \
                 kvs:4.0
    ```
    
    ```bash
    $ docker run -p 13801:13800                                                            \
                 --net=kv_subnet --ip=10.10.0.3 --name="node2"                             \
                 -e ADDRESS="10.10.0.3:13800"                                              \
                 -e VIEW="10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800" \
                 -e REPL_FACTOR=2                                                          \
                 kvs:4.0
    ```
    
    ```bash
    $ docker run -p 13802:13800                                                            \
                 --net=kv_subnet --ip=10.10.0.4 --name="node3"                             \
                 -e ADDRESS="10.10.0.4:13800"                                              \
                 -e VIEW="10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800" \
                 -e REPL_FACTOR=2                                                          \
                 kvs:4.0
    ```
    
    ```bash
    $ docker run -p 13803:13800                                                            \
                 --net=kv_subnet --ip=10.10.0.5 --name="node4"                             \
                 -e ADDRESS="10.10.0.5:13800"                                              \
                 -e VIEW="10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800" \
                 -e REPL_FACTOR=2                                                          \
                 kvs:4.0
    ```

- Stop and remove containers:
  
    ```bash
    $ docker stop node1 node2 node3 node4 && docker rm node1 node2 node3 node4
    ```

# API

## Causal Context

- The format and content of a **causal-context** object is largely up to your team, but a causal context must satisfy the following:

    - It must be expressible as a JSON object, which begins with a left brace and ends with a right brace, { ... } and “is an unordered set of name/value pairs.” (definition from https://json.org).
    
    - It must describe causal history sufficiently for your key-value store to guarantee operations are causally consistent.

- All data operation requests must include the **causal-context** attribute as a top-level key in the JSON body, even if its value is an **empty object** ({}). The **causal-context** attribute should not be nested below another attribute.

- All responses must include the **causal-context** attribute as a top-level key in the JSON body. The **causal-context** attribute should not be nested below another attribute.
  
    - A **causal-context** object from a response becomes the causal context object included in future requests.

    - Keep in mind that you are not implementing client logic, so clients can only propagate causal context objects, they cannot do any processing on them.

    - The **causal-context** provided in a response by the key-value store should always up to date: consecutive read events are still events that may be ordered by happens before.

## Endpoints

- All endpoints will accept JSON content type (“Content-Type: application/json”), and will respond in JSON format and with the appropriate HTTP status code.

- Since your key-value store will have to handle failures, request timeouts are relevant. For now, please make sure that timeouts are 5 seconds or less. This means that any node that does not respond within 5 seconds can broadly or generally be treated as “failed”. Anything less than 5 seconds is within the grader’s purview to test. If your key-value store cannot service a request within a reasonable time frame, please return status code 503 and one of the following JSON:

    - {"error":"Unable to satisfy request","message":"Error in PUT"}
    - {"error":"Unable to satisfy request","message":"Error in GET"}
    - {"error":"Unable to satisfy request","message":"Error in DELETE"}

| Endpoint URI     | accepted request types    |
|------------------|---------------------------|
| /kvs/keys/<key>  | GET, PUT                  |
| /kvs/key-count   | GET                       |
| /kvs/shards      | GET                       |
| /kvs/shards/<id> | GET                       |
| /kvs/view-change | PUT                       |
| /kvs/keys/<key>  | DELETE (for extra credit) |


- For all operations:
  
    - The requests will be sent sequentially.

### Administrative Operations

#### GET key count for a node and the stored replicas

- To get the total number of keys stored by a node, the shards it stores, and the number of keys per shard, send a GET request to the endpoint, **/kvs/key-count** at any node.

    - On success, the response should have status code 200. This example sends the request to node1.

    ```bash
    $ curl --request   GET                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           http://127.0.0.1:13800/kvs/key-count
    
           {
               "message"       : "Key count retrieved successfully",
               "key-count"     : 4,
               "shard-id"      : "1",
           }
           200
    ```

#### GET ID for each shard

- To get information for all shards, send a GET request to the endpoint, **/kvs/shards** at any node. The response should contain the id of each shard.

    - On success, the response should have status code 200.

    ```bash
    $ curl --request   GET                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           http://127.0.0.1:13800/kvs/shards
    
       {
               "message"       : "Shard membership retrieved successfully",
               "shards"        : ["1", "2"]
           }
           200
    ```

#### GET information for a specific shard

- To get the number of keys stored by a shard and what node each replica is stored on, send a GET request to the endpoint, **/kvs/shards/<shard-id>** at any node.

    - On success, the response should have status code 200.

    ```bash
    $ curl --request   GET                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           http://127.0.0.1:13800/kvs/shards/1
    
       {
               "message"       : "Shard information retrieved successfully",
               "shard-id"      : "1",
               "key-count"     : 4,
               "replicas"      : ["10.10.0.2:13800", "10.10.0.3:13800"]
           }
           200
    ```

#### PUT request for view change

- At the begin of testing, one or more nodes will be started with a default view configured by VIEW and REPL_FACTOR. The test script guarantees that the default view is valid so that your kvs should assign shards and replicas to nodes and be able to make response to requests properly without a view change.

- We may add or delete nodes during testing. New nodes will be started with a new view which may configured by different VIEW and REPL_FACTOR. Do not design your view change protocol based on assumptions about what is in the VIEW and REPL_FACTOR environment variables of a newly started node -- the newly started node should not communicate to any other nodes in its own view to trigger view-change.

- To change the view, or add newly started nodes to the key-value store, send a PUT request to the endpoint, /kvs/view-change, with a JSON payload containing the list of addresses in the new view and the replication factor.

- Your kvs only need to guarantee causal consistency among two view-change's.

- A view change requires two operations:

    - Propagating the view update to every node

    - Reshard of the keys (a re-partition of keys across nodes) and potential shuffling of replicas.

    - On success, the response should have status code 200 and JSON:

    ```bash
    $ curl --request   PUT                                                                                          \
           --header    "Content-Type: application/json"                                                             \
           --write-out "%{http_code}\n"                                                                             \
           --data      '{"view":"10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800","repl-factor":2}' \
           http://127.0.0.1:13800/kvs/view-change

           {
               "message" : "View change successful",
               "shards" : [
                   {
                       "shard-id" : "1",
                       "key-count": 4,
                       "replicas" : ["10.10.0.2:13800", "10.10.0.3:13800"]
                   }, {
                       "shard-id" : "2",
                       "key-count": 5,
                       "replicas" : ["10.10.0.4:13800", "10.10.0.5:13800"]
                   }
               ]
           }
           200
    ```
    
    where each element in the “shards” list is a dictionary with three key-value pairs: the “replicas” key maps to a list of IP addresses of nodes storing a replica of the shard, the “key-count” key maps to the number of keys that are assigned to that shard, and the “shard-id” key maps to the ID of the shard. For the above example, the shard with ID 2 has two replicas - node3 at address “10.10.0.4:13800” and node4 at address “10.10.0.5:13800”, and has 5 key-value pairs.

### Key-Value Operations

- For all key-value operations:

    - If a node receiving a request acts as a proxy, its response **should include** the address of the storage node that stores the replica just accessed (if the replica on node3 is accessed, return the address of node3).

    - If a node receiving a request does not act as a proxy (it is the storage node for a replica of the requested key), its response **should not include** the address of the storage node (should not include its own address).
    
    - Different from assignment3, this time, we let **the storage node** verify the keys and values.
    
    - During a network partition, each side of the partition will contain at least one replica from each shard. The test script will propagate **causal-context** through requests. Key-value store should be able to respond to key-value operations with casual-constitency. After the network partition is healed, a gossip protocol should be able to make all replicas converge to newest, correct state.
    
    - If a key-value operation carries **causal-context** that violates casual-consistency, please return status code 400 and one of the following JSON:
    
        - {"error":"Unable to satisfy request","message":"Error in PUT"}
    
        - {"error":"Unable to satisfy request","message":"Error in GET"}
    
        - {"error":"Unable to satisfy request","message":"Error in DELETE"}
    
    - When **replicate_factor > 1**, your gossip protocol should notify all the replicas of a key-value operation within 5 seconds 

- For the below operation descriptions, it is assumed that shard1 (containing node1 and node2) does not store **sampleKey**, and that shard2 (containing node3 and node4) does store **sampleKey**.

#### Insert new key

- To insert a key named sampleKey, send a PUT request to **/kvs/keys/sampleKey** and include the causal context object as JSON.

    - If no value is provided for the new key, the key-value store should respond with status code 400. This example sends the request to node3.

    ```bash
    $ curl --request   PUT                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13802/kvs/keys/sampleKey

           {
               "message"       : "Error in PUT",
               "error"         : "Value is missing",
               "causal-context": new-causal-context-object,
           }
           400
    ```

    - If the key has length greater than 50, the key-value store should respond with status code 400. This example sends the request to node1. Assume that shard2 stores the key **loooooooooooooooooooooooooooooooooooooooooooooooong**, according to the key-partition mechanism. However, node3 from shard2 returns an error message saying the key is too long. 
    
    ```bash
    $ curl --request   PUT                                                              \
           --header    "Content-Type: application/json"                                 \
           --write-out "%{http_code}\n"                                                 \
           --data      '{"value":"sampleValue","causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/loooooooooooooooooooooooooooooooooooooooooooooooong

           {
               "message"       : "Error in PUT",
               "error"         : "Key is too long",
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           400
    ```

    - On success, the key-value store should respond with status code 201. This example sends the request to node1.

    ```bash
    $ curl --request   PUT                                                              \
           --header    "Content-Type: application/json"                                 \
           --write-out "%{http_code}\n"                                                 \
           --data      '{"value":"sampleValue","causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/sampleKey

           {
               "message"       : "Added successfully",
               "replaced"      : false,
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           201
    ```

#### Update existing key

- To update an existing key named sampleKey, send a PUT request to /kvs/keys/sampleKey and include the causal context object as JSON.
  
    - If no updated value is provided for the key, the key-value store should respond with status code 400. This example sends the request to node1.

    ```bash
    $ curl --request   PUT                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/sampleKey

           {
               "message"       : "Error in PUT",
               "error"         : "Value is missing",
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           400
    ```
    
    - The key-value store should respond with status code 200. This example sends the request to node3.

    ```bash
    $ curl --request   PUT                                                              \
           --header    "Content-Type: application/json"                                 \
           --write-out "%{http_code}\n"                                                 \
           --data      '{"value":"sampleValue","causal-context":causal-context-object}' \
           http://127.0.0.1:13802/kvs/keys/sampleKey

           {
               "message"       : "Updated successfully",
               "replaced"      : true,
               "causal-context": new-causal-context-object,
           }
           200
    ```

#### Read an existing key

- To get an existing key named sampleKey, send a GET request to /kvs/keys/sampleKey and include the causal context object as JSON.
  
    - If the key, sampleKey, does not exist, the key-value store should respond with status code 404. The example sends the request to node1.

    ```bash
    $ curl --request   GET                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/sampleKey

           {
               "message"       : "Error in GET",
               "error"         : "Key does not exist",
               "doesExist"     : false,
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           404
    ```

    - On success, assuming the current value of sampleKey is sampleValue, the key-value store should respond with status code 200. This example sends the request to node1.

    ```bash
    $ curl --request   GET                                        \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/sampleKey

           {
               "message"       : "Retrieved successfully",
               "doesExist"     : true,
               "value"         : "sampleValue",
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           200
    ```

#### Remove an existing key (Extra Credit) This feature is now extra credit and not required

- To delete an existing key named sampleKey, send a DELETE request to /kvs/keys/sampleKey and include the causal context object as JSON.

    - If the key, sampleKey, does not exist, the key-value store should respond with status code 404. This example sends the request to node3.

    ```bash
    $ curl --request   DELETE                                     \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13802/kvs/keys/sampleKey

           {
               "message"       : "Error in DELETE",
               "error"         : "Key does not exist",
               "doesExist"     : false,
               "causal-context": new-causal-context-object,
           }
           404
    ```

    - On success, the key-value store should respond with status code 200. This example sends the request to node1.

    ```bash
    $ curl --request   DELETE                                     \
           --header    "Content-Type: application/json"           \
           --write-out "%{http_code}\n"                           \
           --data      '{"causal-context":causal-context-object}' \
           http://127.0.0.1:13800/kvs/keys/sampleKey

           {
               "message"       : "Deleted successfully",
               "doesExist"     : true,
               "address"       : "10.10.0.4:13800",
               "causal-context": new-causal-context-object,
           }
           200
    ```
