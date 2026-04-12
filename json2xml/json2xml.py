'''docstring'''
from pyexpat            import ExpatError               # for fct to_xml
from typing             import Any
from defusedxml.minidom import parseString              # for fct to_xml
from json2xml           import dicttoxml                # for fct to_xml
from .utils             import InvalidDataError         # for fct to_xml
from .utils             import readfromjson

config                  = readfromjson("config.json")
active_profile: str     = config["active"]              # 'dspace' or 'custom'
active_config:  dict    = config[active_profile]

class Json2xml:
    """Wrapper class to convert the data to xml"""

    def __init__(self, data:   dict[str, Any] | list[Any] | None = None,):
        # TODO only (active) config weitergeben?

        # TODO self.bundle          = ...
        self.data                   = data
        self.only_read_folder       =        config["only_read_folder"]         # str           default is ""
        self.not_read_folder        =        config["not_read_folder"]          # str           default is ""

        self.pretty                 = active_config["pretty"]                   # bool          default is True;  new lines + indenting; False gives no string, but bytes
        self.xpath_format           = active_config["xpath_format"]             # bool          default is False

        self.custom_root            = active_config["custom_root"]              # str           default is "root"; wrap output          into a root element, except ""
        # self.wrap_array_items       = active_config["wrap_array_items"]       # bool          default is True;   wrap each array item into a tag;                 TODO use for DS?
        # self.array_items_wrap       = array_items_wrap,                       # fct           default is default_item_func / "item";                              TODO make this work
        self.custom_array_item_wrap = active_config["custom_array_item_wrap"]   # str           default is "";     wrap each array item into this tag,       except ""

        self.array_headers          = active_config["array_headers"]            # bool          default is False; repeat the outer header for each array element;   TODO use for DS?
        self.attr_type              = active_config["attr_type"]                # bool          default is True;  display data type
        self.cdata                  = active_config["cdata"]                    # bool          default is False; wrap string values    into CDATA sections
        self.ids                    = active_config["ids"]                      # list[str]     default is  [];   elements get unique ids; or list[int]?
        self.xml_namespaces         = active_config["xml_namespaces"]           # dict[str, Any] default is {}
                                                                                #                example is {"xsi":{"schemaInstance":            "http://www.w3.org/2001/XMLSchema-instance",
                                                                                #                                   "noNamespaceSchemaLocation": "controlledvocabulary.xsd"
                                                                                #                                   }
                                                                                #                           }

    def exclude( self, dictio: dict[str, Any], not_read_folder: str)              -> dict:
        '''substract folder from dict'''
        smaller_dict:  dict = {}
        for     element in dictio:
            if  element != not_read_folder:
                smaller_dict[element] = dictio[element]
        return  smaller_dict

    def to_xml(  self)                                                            -> Any | None:
        """Convert to xml"""
        if  self.data:
            # TODO this is only necessary for self.pretty!:
            content                             = self.data
            if   isinstance(self.data, dict):
                if      self.only_read_folder   # != "":
                    if  self.only_read_folder  in              self.data:
                        content                 =              self.data[self.only_read_folder]
                elif    self.not_read_folder    # != "":
                        content                 = self.exclude(self.data, self.not_read_folder)
            xml_data = dicttoxml.dicttoxml(
                content,
                self,       # TODO or only config?

                # bundle                          = { 'attr_type':                self.attr_type,
                                                    # 'cdata':                    self.cdata,
                                                    # 'custom_array_item_wrap':   self.custom_array_item_wrap,
                                                    # 'array_headers':            self.array_headers,
                                                    # },
                # xpath_format                    = self.xpath_format,
                # custom_root                     = self.custom_root,
                # # wrap_array_items              = self.wrap_array_items,
                # # array_items_wrap              = self.array_items_wrap,
                # ids                             = self.ids,
                # xml_namespaces                  = self.xml_namespaces,
                # only_read_folder                = self.only_read_folder,
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
