from pyexpat            import ExpatError
from typing             import Any
from defusedxml.minidom import parseString
from json2xml           import dicttoxml
from .utils             import InvalidDataError

# TODO how to apply this? (copy into sync.py?)

class Json2xml:
    """Wrapper class to convert the data to xml"""
    def __init__(
        self,
        data:           dict[str, Any] | list[Any] | None   = None,
        wrapper:        str                                 = "all",
        root:           bool                                = True,
        pretty:         bool                                = True,
        attr_type:      bool                                = True,
        item_wrap:      bool                                = True,
        xpath_format:   bool                                = False,
        cdata:          bool                                = False,
        list_headers:   bool                                = False,
    ):
        self.data           = data
        self.root           = root
        self.wrapper        = wrapper
        self.attr_type      = attr_type
        self.item_wrap      = item_wrap
        self.xpath_format   = xpath_format
        self.cdata          = cdata
        self.list_headers   = list_headers
        self.pretty         = pretty

    def to_xml(self) -> Any | None:
        """Convert to xml using dicttoxml.dicttoxml and then pretty print it."""
        if self.data:
            xml_data = dicttoxml.dicttoxml(
                self.data,
                root=self.root,
                custom_root=self.wrapper,
                attr_type=self.attr_type,
                item_wrap=self.item_wrap,
                xpath_format=self.xpath_format,     # should be last parameter? (see dicttoxml def.)
                cdata=self.cdata,
                list_headers=self.list_headers,
            )
            if self.pretty:
                try:
                    result = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()
                except ExpatError          as   exc:
                    raise InvalidDataError from exc
                return result
            return xml_data
        return None
