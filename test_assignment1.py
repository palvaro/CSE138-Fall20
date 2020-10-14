################### 
# Course: CSE 128
# Date: Fall 2020
# Assignment: #1
# Author: Elisabeth Oliver, Aleck Zhang
# Email: elaolive@ucsc.edu, jzhan293@ucsc.edu
###################

import unittest
import subprocess
import requests

PORT=8081
localhost = "localhost" # Docker Toolbox users should use Docker's ip address here

class TestHW1(unittest.TestCase):

  # Make basic GET http request
  def test1(self):
    res = requests.get('http://'+localhost+':'+str(PORT)+'/hello')
    self.assertEqual(res.text, 'Hello, world!', msg='Incorrect response to /hello endpoint')

  # Send a POST request to app with a parameter, and access that parameter in app
  def test2(self):
    res = requests.post('http://'+localhost+':'+str(PORT)+'/hello/Slugs')
    self.assertEqual(res.text, 'Hello, Slugs!', msg='Incorrect response to POST request to /hello endpoint')

  # Send a POST request to app with a parameter, and access that parameter in app
  def test3(self):
    res = requests.post('http://'+localhost+':'+str(PORT)+'/echo/Hooray!AMessage!123')
    self.assertEqual(res.text, 'POST message received: Hooray!AMessage!123', msg='Incorrect response to POST request to /echo endpoint')

  # Check the status codes
  def test4(self):
    res = requests.get('http://'+localhost+':'+str(PORT)+'/hello')
    self.assertEqual(res.status_code, 200, msg='Did not return status 200 to GET request to /hello endpoint')

    res = requests.post('http://'+localhost+':'+str(PORT)+'/hello')
    self.assertEqual(res.status_code, 405, msg='Did not return status 405 to POST request to /hello endpoint')
    
    res = requests.get('http://'+localhost+':'+str(PORT)+'/echo/foo')
    self.assertEqual(res.status_code, 405, msg='Did not return status 405 to GET request to /echo/<msg> endpoint')

if __name__ == '__main__':
  unittest.main()
