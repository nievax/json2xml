'''docstring'''
from json2xml       import json2xml         # from: folder!
from json2xml.utils import readfromjson

# file_to_test = "./examples/test.json"

# file_to_test = "./examples/booleanjson.json"
# file_to_test = "./examples/booleanjson2.json"

# file_to_test = "./examples/bigexample.json"
# file_to_test = "./examples/light.json"
# file_to_test = "./examples/wrongjson.json"

config              = readfromjson("config.json")
file_to_transform   = config["file_to_transform"]
data                = readfromjson(file_to_transform)

print(json2xml.Json2xml(data).to_xml())
