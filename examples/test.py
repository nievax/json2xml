'''docstring'''
from json2xml       import json2xml
from json2xml.utils import readfromjson

file_to_test = "test.json"

# file_to_test = "booleanjson.json"
# file_to_test = "booleanjson2.json"

# file_to_test = "bigexample.json"
# file_to_test = "licht.json"
# file_to_test = "wrongjson.json"

data = readfromjson(file_to_test)
print(json2xml.Json2xml(data).to_xml())
