'''docstring'''
from pyexpat            import ExpatError
from typing             import Any
from defusedxml.minidom import parseString
from json2xml           import dicttoxml
from .utils             import InvalidDataError

class Json2xml:
    """Wrapper class to convert the data to xml"""

    def __init__(
        self,
        data:           dict[str, Any] | list[Any] | None   = None,

        xpath_format:   bool                                = True,

        root:           bool                                = True,     # use the wrapper (as root)?
        wrapper:        str                                 = "all",

        attr_type:      bool                                = False,    # display value type?
        item_wrap:      bool                                = False,    # nest each item in array into <item/>?
        cdata:          bool                                = False,    # should string values be wrapped in CDATA sections?
        list_headers:   bool                                = False,    # repeat the header for every element in a list?

        pretty:         bool                                = False,    # new lines + indenting
    ):
        self.data           = data
        self.xpath_format   = xpath_format
        self.root           = root
        self.wrapper        = wrapper
        self.attr_type      = attr_type
        self.item_wrap      = item_wrap
        self.cdata          = cdata
        self.list_headers   = list_headers
        self.pretty         = pretty

    def to_xml(self) -> Any | None:
        """Convert to xml using"""
        if self.data:
            xml_data = dicttoxml.dicttoxml(
                self.data,
                xpath_format    = self.xpath_format,
                root            = self.root,
                custom_root     = self.wrapper,
                attr_type       = self.attr_type,
                item_wrap       = self.item_wrap,
                cdata           = self.cdata,
                list_headers    = self.list_headers,
            )
            if self.pretty:
                try:
                    result = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()
                except ExpatError          as   exc:
                    raise InvalidDataError from exc
                return result
            return xml_data
        return None
