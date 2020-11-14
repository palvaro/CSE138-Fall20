################### 
# Course: CSE 138
# Date: Fall 2020
# Assignment: #3
# Author: Aleck Zhang
# Email: jzhan293@ucsc.edu
###################

import unittest
import subprocess
import requests # Note, you may need to install this package via pip (or pip3)

nodes = [
	{},
	{
		"addr": "10.10.0.4:13800",
		"port": 13801,
	},
	{
		"addr": "10.10.0.5:13800",
		"port": 13802,
	},
	{
		"addr": "10.10.0.6:13800",
		"port": 13803,
	},
]

localhost = "localhost" # windows toolbox users will again want to make this the docker machine's ip adress

class Client():

	def putKey(self, key, value, port):
		result = requests.put('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),
							  json={'value':value},
							  headers = {"Content-Type": "application/json"})
		print("PUT key result %s"%str(result.content))
		return self.formatResult(result)

	def getKey(self, key, port):
		result = requests.get('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),
							  json={},
							  headers = {"Content-Type": "application/json"})
		print("GET key result %s"%str(result.content))

		return self.formatResult(result)

	def viewChange(self, view, port):
		result = requests.put('http://%s:%s/kvs/view-change'%(localhost, str(port)),
							  json={"view":str(view)},
							  headers = {"Content-Type": "application/json"})
		print("PUT view-change result %s"%str(result.content))

		return self.formatResult(result)

	def keyCount(self, port):
		result = requests.get('http://%s:%s/kvs/key-count'%(localhost, str(port)),
							  json={},
							  headers = {"Content-Type": "application/json"})
		print("GET key-count result %s"%str(result.content))

		return self.formatResult(result)

	def deleteKey(self, key, port):
		result = requests.delete('http://%s:%s/kvs/keys/%s'%(localhost, str(port), key),
								 json={},
								 headers = {"Content-Type": "application/json"})
		print("DELETE key result %s"%str(result.content))

		return self.formatResult(result)

	# this just turns the requests result object into a simplified json object
	# containing only fields I care about
	def formatResult(self, result):
		status_code = result.status_code

		result = result.json()

		if result != None:
			jsonKeys = ["message", "replaced", "error", "doesExist", "value", "key-count", "shards", "address"]
			result = {k:result[k] for k in jsonKeys if k in result}

			result["status_code"] = status_code
		else:
			result = {"status_code": status_code}

		return result

client = Client()

#### Expected Responses:
addResponse_Success = { 	"message":		"Added successfully",
						   "replaced": 	False,
						   "status_code":	201}
addResponseError_NoValue = {"error":	"Value is missing",
							"message":	"Error in PUT",
							"status_code":	400}
addResponseError_NoKey = {	"error":	"Value is missing",
							  "message":	"Error in PUT",
							  "status_code":	400}
addResponseError_longKey = {"error":	"Key is too long",
							"message":	"Error in PUT",
							"status_code":	400}

updateResponse_Success = {"message":		"Updated successfully",
						  "replaced":		True,
						  "status_code":	200}
updateResponseError_NoKey = addResponseError_NoKey
updateResponseError_NoValue = addResponseError_NoValue

getResponse_Success = {	"doesExist":	True,
						   "message":		"Retrieved successfully",
						   "value":		"Default Value, should be changed based on input",
						   "status_code":	200}
getResponse_NoKey = {	"doesExist":	False,
						 "error":		"Key does not exist",
						 "message":		"Error in GET",
						 "status_code":	404}

delResponse_Success = {	"doesExist":	True,
						   "message":		"Deleted successfully",
						   "status_code":	200}
delResponse_NoKey = {	"doesExist":	False,
						 "error":		"Key does not exist",
						 "message":		"Error in DELETE",
						 "status_code":	404}

getKeyCountResponse_Success = {
						   "message":		"Key count retrieved successfully",
						   "status_code":	200}

class TestHW3(unittest.TestCase):
	def check_node_id(self, result, node_id, num):
		if "address" in result: # the receiving node does not store the key
			node_id_ = 0
			for i in range(1,num+1):
				if nodes[i]["addr"] == result["address"]:
					node_id_ = i
					break
			self.assertNotEqual(node_id_,0) # node_id must be found
			self.assertNotEqual(node_id_,node_id) # node_id should not equal to the receiving node

			return node_id_

		return node_id

	def check_key_count(self, result):
		self.assertTrue("key-count" in result)

		return int(result["key-count"])

	def check_view_change(self, result, num):
		self.assertTrue("shards" in result)
		shards = result["shards"]
		self.assertEqual(len(shards),num)

		key_counts = [0] * num
		total_keys = 0
		for i in range(num):
			shard = shards[i]
			self.assertTrue("address" in shard)

			node_id = 0
			for j in range(1,num+1):
				if nodes[j]["addr"] == shard["address"]:
					node_id = j
					break

			self.assertNotEqual(node_id,0)
			key_count = self.check_key_count(shard)
			key_counts[node_id-1] = key_count
			total_keys += key_count

		return key_counts, total_keys

	def get_key_counts(self, num):
		key_counts = []
		total_keys = 0

		for i in range(1,num+1):
			result = client.keyCount(nodes[i]["port"])
			key_count = self.check_key_count(result)
			key_counts.append(key_count)
			total_keys += key_count

		return key_counts, total_keys

	def assertEqual_helper(self, a, b):
		a = a.copy()
		a.pop("address",None)
		self.assertEqual(a,b)

	# (add, update, get, key-count, delete, key-count)'s
	def test_1(self):
		keys = 100
		for i in range(keys):
			id1,id2 = 1,2
			if i%2 == 0:
				id1,id2 = 2,1

			key = "test_1_%d"%i
			value = "a friendly string %d"%i

			# add
			result = client.putKey(key,value,nodes[id1]["port"])
			self.assertEqual_helper(result,addResponse_Success)
			# update
			result = client.putKey(key,value,nodes[id1]["port"])
			self.assertEqual_helper(result,updateResponse_Success)
			# get
			result = client.getKey(key,nodes[id2]["port"])
			expected = getResponse_Success.copy()
			expected["value"] = value
			self.check_node_id(result,id2,2)
			self.assertEqual_helper(result,expected)
			# key-count
			key_counts, total = self.get_key_counts(2)
			self.assertEqual(total, 1)
			# delete
			result = client.deleteKey(key, nodes[id2]["port"])
			self.check_node_id(result,id2,2)
			self.assertEqual_helper(result, delResponse_Success)
			# key-count
			key_counts, total = self.get_key_counts(2)
			self.assertEqual(total, 0)

	# add's, key-count, view-change, delete's, key-count
	def test_2(self):
		keys = 100

		# add's
		for i in range(keys):
			id = 1
			if i%2 == 0:
				id = 2
			result = client.putKey("test_2_%d"%i,"a friendly string %d"%i,nodes[id]["port"])
			self.assertEqual_helper(result,addResponse_Success)

		# key-count
		key_counts1, total1 = self.get_key_counts(2)
		self.assertEqual(total1, keys)
		# view-change
		result = client.viewChange("10.10.0.4:13800,10.10.0.5:13800,10.10.0.6:13800",nodes[1]["port"])
		key_counts2, total2 = self.check_view_change(result,3)
		self.assertEqual(total2, keys)
		print(key_counts1, "===>", key_counts2)
		# todo: check if shards are balanced

		# delete's
		for i in range(keys):
			id = i%3
			if id == 0:
				id = 3

			key = "test_2_%d"%i
			result = client.deleteKey(key, nodes[id]["port"])
			self.check_node_id(result,id,3)
			self.assertEqual_helper(result, delResponse_Success)
		# key-count
		key_counts3, total3 = self.get_key_counts(3)
		self.assertEqual(total3, 0)

if __name__ == '__main__':
	unittest.main()
