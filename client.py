import requests # Note, you may need to install this package via pip (or pip3)

localhost = "localhost"
timeout = 5

class Client():
    def __init__(self,causal_context_flag=True,print_response=False):
        self.causal_context = {}
        self.causal_context_flag = causal_context_flag
        self.print_response = print_response

    def putKey(self, key, value, port):
        result = requests.put('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),timeout=timeout,
                              json={'value':value,'causal-context':self.causal_context},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("PUT key result %s"%str(result.content))

        return self.formatResult(result)

    def getKey(self, key, port):
        result = requests.get('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),timeout=timeout,
                              json={'causal-context':self.causal_context},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("GET key result %s"%str(result.content))

        return self.formatResult(result)

    def viewChange(self, view, repl_factor, port):
        result = requests.put('http://%s:%s/kvs/view-change'%(localhost, str(port)),timeout=timeout,
                              json={"view":str(view),'repl-factor':repl_factor},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("PUT view-change result %s"%str(result.content))

        return self.formatResult(result)

    def keyCount(self, port):
        result = requests.get('http://%s:%s/kvs/key-count'%(localhost, str(port)),timeout=timeout,
                              json={},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("GET key-count result %s"%str(result.content))

        return self.formatResult(result)

    def getShards(self, port):
        result = requests.get('http://%s:%s/kvs/shards'%(localhost, str(port)),timeout=timeout,
                              json={},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("GET shards result %s"%str(result.content))

        return self.formatResult(result)

    def getShard(self, port, shard_id):
        result = requests.get('http://%s:%s/kvs/shards/%s'%(localhost, str(port), str(shard_id)),timeout=timeout,
                              json={},
                              headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("GET shard by shard-id result %s"%str(result.content))

        return self.formatResult(result)

    def deleteKey(self, key, port):
        result = requests.delete('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),timeout=timeout,
                                 json={'causal-context':self.causal_context},
                                 headers = {"Content-Type": "application/json"})

        if self.print_response:
            print("DELETE key result %s"%str(result.content))

        return self.formatResult(result)

    # this just turns the requests result object into a simplified json object
    # containing only fields I care about
    def formatResult(self, result):
        status_code = result.status_code

        result = result.json()

        if result != None:
            # jsonKeys = ["message", "replaced", "error", "doesExist", "value", "key-count", "shards", "address"]
            # result = {k:result[k] for k in jsonKeys if k in result}

            result["status_code"] = status_code

            if "causal-context" in result:
                if self.causal_context_flag:
                    self.causal_context = result["causal-context"]

                result.pop("causal-context")
        else:
            result = {"status_code": status_code}

        return result
