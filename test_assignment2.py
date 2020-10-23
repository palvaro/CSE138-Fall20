################### 
# Course: CSE 138
# Date: Fall 2020
# Assignment: #2
# Author: Elisabeth Oliver, Aleck Zhang
# Email: elaolive@ucsc.edu, jzhan293@ucsc.edu
###################

import unittest
import subprocess
import requests # Note, you may need to install this package via pip (or pip3)

PORT = 13800
localhost = "localhost" # windows toolbox users will again want to make this the docker machine's ip adress

class Client():

	def putKey(self, key, value, port):
		result = requests.put('http://%s:%s/kvs/%s'%(localhost, str(port), key),
							json={'value':value},
							headers = {"Content-Type": "application/json"})
		return self.formatResult(result)
	
	def getKey(self, key, port):
		result = requests.get('http://%s:%s/kvs/%s'%(localhost, str(port), key),
							headers = {"Content-Type": "application/json"})
		return self.formatResult(result)
	
	def deleteKey(self, key, port):
		result = requests.delete('http://%s:%s/kvs/%s'%(localhost, str(port), key),
							headers = {"Content-Type": "application/json"})
		return self.formatResult(result)

	# this just turns the requests result object into a simplified json object 
	# containing only fields I care about 
	def formatResult(self, result):
		status_code = result.status_code
		result = result.json()

		if result != None:			
			jsonKeys = ["message", "replaced", "error", "doesExist", "value"]
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



class TestHW1(unittest.TestCase):

### Add New Keys
	# add a new key
	def test_add_1(self):
		result = client.putKey("Test", "a friendly string", PORT)

		self.assertEqual(result, addResponse_Success)

## Get Key Values
	# add and get
	def test_get_2(self):
		key = "AKey"
		value = "a different friendly string"

		result = client.putKey(key, value, PORT)

		self.assertEqual(result["status_code"], addResponse_Success["status_code"], 
			msg="add key: failed add, cannot continue test\n%s\n"%result)


		result = client.getKey(key, PORT)
		expected = getResponse_Success.copy()
		expected["value"] = value

		self.assertEqual(result, expected)

# ### Update Keys
	# add then update
	def test_update_1(self):
		key = "AValueToUpdate!"

		result = client.putKey(key, "one, one, one, one!", PORT)

		self.assertEqual(result["status_code"], addResponse_Success["status_code"], 
			msg="add key: failed add, cannot continue test\n%s\n"%result)
		

		result = client.putKey(key, "two, three, four!", PORT)

		self.assertEqual(result, updateResponse_Success)

### Delete Keys
	# add and delete
	def test_del_1(self):
		key = "keyToDelete"

		result = client.putKey(key, "delete, delete, delete!", PORT)

		self.assertEqual(result["status_code"], addResponse_Success["status_code"], 
			msg="add key: failed add, cannot continue test\n%s\n"%result)

		result = client.deleteKey(key, PORT)

		self.assertEqual(result, delResponse_Success)


if __name__ == '__main__':
	unittest.main()
