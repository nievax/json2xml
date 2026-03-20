'''docstring'''
from json2xml       import json2xml
from json2xml.utils import readfromjson

data = readfromjson("test.json")

# data = readfromjson("./examples/booleanjson.json")
# data = readfromjson("./examples/booleanjson2.json")

# data = readfromjson("./examples/bigexample.json")
# data = readfromjson("./examples/licht.json")
# data = readfromjson("./examples/wrongjson.json")

print(json2xml.Json2xml(data).to_xml())
