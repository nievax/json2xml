'''docstring'''
from pyexpat            import ExpatError               # for fct to_xml
from typing             import Any
from defusedxml.minidom import parseString              # for fct to_xml
from json2xml           import dicttoxml                # for fct to_xml
from .utils             import InvalidDataError         # for fct to_xml

class Json2xml:
    """Wrapper class to convert the data to xml"""

    def __init__(
        self,
        data:           dict[str, Any] | list[Any] | None   = None,
        config:         dict                                = {},
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

    def to_xml(self) -> Any | None:
        """Convert to xml"""
        if self.data:
            xml_data = dicttoxml.dicttoxml(
                self.data,
                xpath_format            = self.xpath_format,
                use_root                = self.use_root,
                custom_root             = self.custom_root,
                wrap_array_items        = self.wrap_array_items,
                # array_items_wrap      = self.array_items_wrap,
                custom_array_item_wrap  = self.custom_array_item_wrap,
                array_headers           = self.array_headers,
                attr_type               = self.attr_type,
                cdata                   = self.cdata,
                ids                     = self.ids,
                xml_namespaces          = self.xml_namespaces,
            )
            if self.pretty:
                try:
                    return_name = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()
                except ExpatError          as   exc:
                    raise InvalidDataError from exc
            else:
                return_name = xml_data
        else:
                return_name = None
        return  return_name
