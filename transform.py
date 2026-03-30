'''docstring'''
from json2xml       import json2xml         # from: folder!
from json2xml.utils import readfromjson

def write_file(    path: str, cont)                      -> None:
    ''''write content to file in path'''
    with open(path, "w", encoding="utf-8") as file:             # includes file closing
        file.write(cont)

# options for config.json:
# ==========================
# path_to_transform = "./examples/test"

# path_to_transform = "./examples/booleanjson"
# path_to_transform = "./examples/booleanjson2"

# path_to_transform = "./examples/bigexample"
# path_to_transform = "./examples/light"
# path_to_transform = "./examples/wrongjson"

config              = readfromjson("config.json")

transform_path      = config[     "path_to_transform"]
json_data           = readfromjson(transform_path + ".json")

xml_data            = json2xml.Json2xml(json_data).to_xml()
write_path          =              transform_path + ".xml"

write_file(write_path, xml_data)
print(                 xml_data)
