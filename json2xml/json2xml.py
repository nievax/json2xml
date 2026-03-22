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

        xpath_format:   bool        = False,    # default is False

        use_root:       bool        = True,     # default is True;  the output is wrapped into an XML root element
        root:           str         = "all",    # default is "root"

        attr_type:      bool        = False,    # default is True;  display data type
        cdata:          bool        = False,    # default is False; wrap string values into CDATA sections
        ids:            list | None = None,     # default is None / [];  elements get unique ids
        xml_namespaces: dict | None = None,     # default is None / {}
        array_headers:  bool        = False,    # default is False; repeat the outer header for each array element;   TODO use for DS?

        wrap_array_items: bool      = True,     # default is True;  wrap each array item into a tag;                  TODO use for DS?
        # array_items_wrap: fct       = ??,     # default is default_item_func / "item";                              TODO make this work
        custom_array_item_wrap: str = "node",

        pretty:         bool        = True,     # new lines + indenting; False gives no string, but bytes
    ):
        self.data                   = data
        self.xpath_format           = xpath_format
        self.use_root               = use_root
        self.root                   = root
        self.attr_type              = attr_type
        self.wrap_array_items       = wrap_array_items
        # self.array_items_wrap       = array_items_wrap,
        self.custom_array_item_wrap = custom_array_item_wrap
        self.cdata                  = cdata
        self.ids                    = ids
        self.xml_namespaces         = xml_namespaces
        self.array_headers          = array_headers
        self.pretty                 = pretty

    def to_xml(self) -> Any | None:
        """Convert to xml"""
        if self.data:
            xml_data = dicttoxml.dicttoxml(
                self.data,
                xpath_format            = self.xpath_format,
                use_root                = self.use_root,
                custom_root             = self.root,
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
                    result = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()
                except ExpatError          as   exc:
                    raise InvalidDataError from exc
                return result
            return xml_data
        return None
