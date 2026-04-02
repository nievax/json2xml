'''docstring'''
from pyexpat            import ExpatError               # for fct to_xml
from typing             import Any
from defusedxml.minidom import parseString              # for fct to_xml
from json2xml           import dicttoxml                # for fct to_xml
from .utils             import InvalidDataError         # for fct to_xml
from .utils             import readfromjson

config = readfromjson("config.json")

class Json2xml:
    """Wrapper class to convert the data to xml"""

    def __init__(
        self,
        data:           dict[str, Any] | list[Any] | None   = None,
    ):
        self.data                   = data
        self.xpath_format           = config["xpath_format"]            # bool          default is False
        self.use_root               = config["use_root"]                # bool          default is True;  the output is wrapped into an XML root element
        self.custom_root            = config["custom_root"]             # str           default is "root"
        self.attr_type              = config["attr_type"]               # bool          default is True;  display data type
        self.wrap_array_items       = config["wrap_array_items"]        # bool          default is True;  wrap each array item into a tag;                  TODO use for DS?
        # self.array_items_wrap       = array_items_wrap,               # fct           default is default_item_func / "item";                              TODO make this work
        self.custom_array_item_wrap = config["custom_array_item_wrap"]  # see above
        self.cdata                  = config["cdata"]                   # bool          default is False; wrap string values into CDATA sections
        self.ids                    = config["ids"]                     # list | None   default is None / [];  elements get unique ids
        self.xml_namespaces         = config["xml_namespaces"]          # dict | None   default is None / {}
        self.array_headers          = config["array_headers"]           # bool          default is False; repeat the outer header for each array element;   TODO use for DS?
        self.pretty                 = config["pretty"]                  # bool          default is True;  new lines + indenting; False gives no string, but bytes
        self.only_read_folder       = config["only_read_folder"]        # str           default is ""
        self.not_read_folder        = config["not_read_folder"]         # str           default is ""

    def exclude(self, dictio: dict, not_read_folder: str)                        -> dict:
        '''substract folder from dict'''
        smaller_dict:  dict = {}
        for     element in dictio:
            if  element != not_read_folder:
                smaller_dict[element] = dictio[element]
        return  smaller_dict

    def to_xml(self) -> Any | None:
        """Convert to xml"""
        if  self.data:
            # TODO this is only necessary for self.pretty!:
            content                             = self.data
            if   isinstance(self.data, dict):
                if      self.only_read_folder  != "":
                    if  self.only_read_folder  in              self.data:
                        content                 =              self.data[self.only_read_folder]
                elif    self.not_read_folder   != "":
                        content                 = self.exclude(self.data, self.not_read_folder)
            xml_data                            = dicttoxml.dicttoxml(
                        content,
                xpath_format                    = self.xpath_format,
                use_root                        = self.use_root,
                custom_root                     = self.custom_root,
                wrap_array_items                = self.wrap_array_items,
                # array_items_wrap              = self.array_items_wrap,
                custom_array_item_wrap          = self.custom_array_item_wrap,
                array_headers                   = self.array_headers,
                attr_type                       = self.attr_type,
                cdata                           = self.cdata,
                ids                             = self.ids,
                xml_namespaces                  = self.xml_namespaces,
                only_read_folder                = self.only_read_folder,
                not_read_folder                 = self.not_read_folder,
            )
            if self.pretty:
                try:
                    return_value                = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()
                except ExpatError              as exc:
                    raise InvalidDataError   from exc
            else:
                    return_value                =             xml_data
        else:
                    return_value                = None
        return      return_value
