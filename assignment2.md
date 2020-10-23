# Instructions

### Course
CSE 138: Distributed Systems

### Date
- Due     : Firday, 11/04/20

### General

- You must do your own individual work and submit this assignment as an individual.

- You should get started to form a group of 2-4 people for future assignments.

- You may not use an existing key-value store (e.g. Redis, MongoDB, etc.)

- You will build a **RESTful multi-site key-value store**.

    - The key-value store must be able to:

        1. Insert a new key-value pair.

        1. Update the value of an existing key.

        1. Get the value of an existing key.

        1. Delete an existing key from the store.

    - The key-value store must run as a collection of communicating instances:

        1. One **main** instance directly responds client and forwarded requests.

        1. Many **follower** instances:

            1. forward requests from a client (the **originating client**) to the main instance.

            1. forward responses from the main instance to the **originating client**.

- You will use **Docker** to create a container that runs the RESTful multi-site key-value store at
  port 13800.

- Your key-value store does not need to persist the data (in-memory only is acceptable).


### Building and testing your container {#building-testing}

- We provide a test script, `test_assignment2.py`, that you **should** use to test your work.

- The provided tests are similar to the tests we will use to evaluate your submitted assignment.


### Submission workflow

- Create a private repository.

    - For simplicity, the repository may be named `cse138_assignment2`.

    - If you wish to reuse your assignment1 repository, for future
      assignments, we recommend the use of tags for marking the final version of each assignment
      and branches for active development. Some helpful links:

        - For tagging repositories: https://git-scm.com/book/en/v2/Git-Basics-Tagging

        - For branch fundamentals:
          https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging

        - A "simple" strategy for branch management:
          https://nvie.com/posts/a-successful-git-branching-model/#the-main-branches

- The Github accounts of `ucsc-cse138-staff` should be added as collaborators to the repository.

- The repository should contain:

    - The `Dockerfile` defining how to build your Docker image.

    - The project file(s) implementing the key-value store.

- Submit your CruzID, repository URL, and the commit ID (aka commit hash) to be evaluated here:
    https://forms.gle/HW3dqMzijjB4QMRWA
        
    - **For full credit**, you will also need to submit a list of names and cruzIDs of your teammates.
    
    - The commit timestamp **must be no later than 11/04/2020 11:59 PM PDT**

    - The google form must be submitted within a reasonable time of the due date (preferably 10
      minutes).

    - Late submissions are accepted, with a 10% penalty for every 24 hours after the above
      deadline.


### Evaluation and grading {#evaluating-grading}

- To evaluate the assignment, the course staff will run your project using Docker

- We will check that your key-value store will send the correct response and status codes in
  response to GET, PUT, and DELETE requests.


# Key-Value Store REST API

### Endpoints

- `/kvs/<key>` will accept GET, PUT, and DELETE requests with JSON content type. The response
  will be in JSON format and return a status code as appropriate.

##### Insert new key

- To insert a key named `sampleKey`, send a PUT request to /kvs/sampleKey. The key-value store
  should respond with status code 201 and JSON:
  `{"message":"Added successfully","replaced":false}`.

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{"value": "sampleValue"}'        \
           http://127.0.0.1:13800/kvs/sampleKey

    {"message":"Added successfully","replaced":false}
    201
```

- If no value is provided for the new key, the key-value store should respond with status code 400
  and JSON: `{"error":"Value is missing","message":"Error in PUT"}`.

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{}'                              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"error":"Value is missing","message":"Error in PUT"}
    400
```

- If the value provided for the new key has length greater than 50, the key-value store should
  respond with status code 400 and JSON: `{"error":"Key is too long","message":"Error in PUT"}`.

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{"value": "sampleValue"}'        \
           http://127.0.0.1:13800/kvs/6TLxbmwMTN4hX7L0QX5NflWH0QKfrTlzcuM5PUQHS52lCizKbEM

    {"error":"Key is too long","message":"Error in PUT"}
    400
```


##### Update existing key

- To update an existing key named `sampleKey`, send a PUT request to `/kvs/sampleKey`. The
  key-value store should respond with status code 200 and JSON:
  `{"message":"Updated successfully","replaced":true}`

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{"value": "updatedValue"}'       \
           http://127.0.0.1:13800/kvs/sampleKey

      {"message":"Updated successfully","replaced":true}
      200
```

- If no updated value is provided for the key, the key-value store should respond with status code
  400 and JSON: `{"error":"Value is missing","message":"Error in PUT"}`

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{}'                              \
           http://127.0.0.1:13800/kvs/sampleKey

     {"error":"Value is missing","message":"Error in PUT"}
     400
```


##### Read an existing key

- To get an existing key named `sampleKey`, send a GET request to `/kvs/sampleKey`.

    - Assuming the current value of `sampleKey` is `sampleValue`, the key-value store should
      respond with status code 200 and JSON:
      `{"doesExist":true,"message":"Retrieved successfully","value":"sampleValue"}`

    - If the value of `sampleKey` has been updated to `updatedValue` (as in the "Update existing
      key" example above), then the key-value store should respond with status code 200 and JSON:
      `{"doesExist":true,"message":"Retrieved successfully","value":"updatedValue"}`

```bash
    $ curl --request   PUT                               \
           --header    "Content-Type: application/json"  \
           --write-out "%{http_code}\n"                  \
           --data      '{"value": "sampleValue"}'        \
           http://127.0.0.1:13800/kvs/sampleKey

    {"message":"Added successfully","replaced":false}
    201

    $ curl --request GET                             \
           --header "Content-Type: application/json" \
           --write-out "%{http_code}\n"              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"doesExist":true,"message":"Retrieved successfully","value":"sampleValue"}
    200

    $ curl --request   PUT                              \
           --header    "Content-Type: application/json" \
           --write-out "%{http_code}\n"                 \
           --data      '{"value": "updatedValue"}'      \
           http://127.0.0.1:13800/kvs/sampleKey

    {"message":"Updated successfully","replaced":true}
    200

    $ curl --request GET                             \
           --header "Content-Type: application/json" \
           --write-out "%{http_code}\n"              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"doesExist":true,"message":"Retrieved successfully","value":"updatedValue"}
    200
```

- If the key, `sampleKey`, does not exist, the key-value store should respond with status code 404
  and the JSON: `{"doesExist":false,"error":"Key does not exist","message":"Error in GET"}`

```bash
    $ curl --request GET                             \
           --header "Content-Type: application/json" \
           --write-out "%{http_code}\n"              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"doesExist":false,"error":"Key does not exist","message":"Error in GET"}
    404
```


##### Remove an existing key

- To delete an existing key named `sampleKey`, send a DELETE request to `/kvs/sampleKey`. The
  key-value store should respond with status code 200 and JSON:
  `{"doesExist":true,"message":"Deleted successfully"}`

```bash
    $ curl --request DELETE                          \
           --header "Content-Type: application/json" \
           --write-out "%{http_code}\n"              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"doesExist":true,"message":"Deleted successfully"}
    200
```

- If the key, `sampleKey`, does not exist, the key-value store should respond with status code 404
  and JSON: `{"doesExist":false,"error":"Key does not exist","message":"Error in DELETE"}`

```bash
    $ curl --request DELETE                          \
           --header "Content-Type: application/json" \
           --write-out "%{http_code}\n"              \
           http://127.0.0.1:13800/kvs/sampleKey

    {"doesExist":false,"error":"Key does not exist","message":"Error in DELETE"}
    404
```


# Main and Forwarding Roles for Multi-site coordination

### Description

```
        +--------+                             +------+
        | client |                             | main |
        +--------+                             +------+
            |                                    |
            | ---------------request-----------> |
            | <--------------response----------- |
            |                                    |
            |                                    |
            |             +----------+           |
            |             | follower |           |
            |             +----------+           |
            |                  |                 |
            | ----request--->  |                 |
            |                  | ---request--->  |
            |                  | <---response--- |
            | <---response---  |                 |
            |                  |                 |
            v                  v                 v
```

You will implement a key-value store that may be started as either: a **main** instance or a
**follower** instance. Your key-value store will check the value of the environment variable,
`FORWARDING_ADDRESS` to determine its role:

- If `FORWARDING_ADDRESS` is empty, the instance is the **main** instance.

- Otherwise, the instance is a **follower** instance.

- The main instance should always respond directly to requests.

- The follower instance should forward requests to the main instance, then forward the response to
  the client. If the follower instance does not receive a response from the main instance the
  response to the client must have status code 503 and one of the following JSON:

    - `{"error":"Main instance is down","message":"Error in PUT"}`

    - `{"error":"Main instance is down","message":"Error in GET"}`

    - `{"error":"Main instance is down","message":"Error in DELETE"}`

# Docker Network Management

In the following, we explain a scenario where we have one main instance, one follower instance,
and a Docker subnet named **kv_subnet**.

- Create subnet, `kv_subnet`, with IP range `10.10.0.0/16`:

```bash
    $ docker network create --subnet=10.10.0.0/16 kv_subnet
```

- Build Docker image containing the key-value store implementation:

```bash
    $ docker build -t kvs:2.0 <path-to-Dockerfile-directory>
```

- Run the main instance at `10.10.0.2:13800` in a Docker container named `main-instance`:

```bash
    $ docker run -p 13800:13800 --net=kv_subnet --ip=10.10.0.2 --name="main-instance" kvs:2.0
```

- Run the follower instance at `10.10.0.3:13800` in a Docker container named `follower-instance`,
which will forward requests to the main instance:

```bash
    $ docker run -p 13801:13800                          \
                 --net=kv_subnet                         \
                 --ip=10.10.0.3                          \
                 --name="follower-instance"              \
                 -e FORWARDING_ADDRESS="10.10.0.2:13800" \
                 kvs:2.0
```

- Stop and remove containers:

```bash
    $ docker stop main-instance
    $ docker stop follower-instance
    $ docker rm main-instance
    $ docker rm follower-instance
```
