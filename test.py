'''docstring'''
from json2xml       import json2xml         # from: folder!
from json2xml.utils import readfromjson

config       = readfromjson("config.json")

file_to_test = "./examples/test.json"

# file_to_test = "./examples/booleanjson.json"
# file_to_test = "./examples/booleanjson2.json"

# file_to_test = "./examples/bigexample.json"
# file_to_test = "./examples/light.json"
# file_to_test = "./examples/wrongjson.json"

data           = readfromjson(file_to_test)

print(json2xml.Json2xml(data, config).to_xml())
