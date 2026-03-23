"""
    function dicttoxml (see below) converts a python object into XML.

    :param dict obj:

    :param bool use_root:
        output is wrapped in an XML root element
        default is True

    :param str custom_root:
        specify a custom root element
        default is 'root'

    :param bool wrap_array_items:
        warp each array item into a tag
        default is True

        ..python

            data = {'bike': ['blue', 'green']}

        .. xml

            Example if True:

            <bike>
                <item>
                    blue
                </item>
                <item>
                    green
                </item>
            </bike>

            Example if False:

            <bike>
                    blue
            </bike>
            <bike>
                    green
            </bike>'

    # :param Callable array_items_wrap:
    #     how to generate the tag for each array item
    #     default is default_item_func resp. 'item'

    :param str custom_array_item_wrap:
        the tag for each array item
        default is 'item'

    :param bool array_headers:
        repeats the header for each array element
        default is False 
        
        .. python

            "Bike": [
                {'frame_color': 'red'},
                {'frame_color': 'green'}
            ]

        .. xml

            Example if True:

            <Bike>
                <frame_color>
                    red
                </frame_color>
            </Bike>
            <Bike>
                <frame_color>
                    green
                </frame_color>
            </Bike>

    :param bool ids:
        elements get unique ids
        default is False

    :param bool attr_type:
        elements get a data type attribute
        default is True

    :param bool cdata:
        wrap string values into CDATA
        default is False

    :param dict xml_namespaces:
        key is  xmlns prefix and value the URN
        default is {}
        Example:

        .. python

            { 'flex': "http://www.w3.org/flex/flexBase",
              'xsl':  "http://www.w3.org/1999/XSL/Transform",
            }

        .. xml

            <root xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                  xmlns:flex="http://www.w3.org/flex/flexBase">

    :param bool xpath_format:
        default is False
        When True, produces XPath 3.1 json-to-xml compliant output as specified
        by W3C (https://www.w3.org/TR/xpath-functions-31/#func-json-to-xml).
        Uses type-based element names (map, array, string, number, boolean, null)
        with key attributes and the http://www.w3.org/2005/xpath-functions namespace.

        Example:

        .. python

            {"name": "John",
             "age":  30,
            }

        .. xml

            <map xmlns="http://www.w3.org/2005/xpath-functions">
                <string key="name">
                    John
                </string>
                <number key="age">
                    30
                </number>
            </map>


    # #####################################################################
    
    Dictionary-keys with special char '@' have special meanings:

    @attrs: This allows custom xml attributes:

    .. python

        {'@attr':   {'a':'b'},
         'x':        'y',
        }

    .. code-block:: xml

        <root a="b">
            <x>
                y
            </x>
        </root>

    @flat: If a key ends with @flat (or dict contains key '@flat'),
    encapsulating node is omitted. Similar to wrap_array_items.

    @val: @attrs requires complex dict type. If primitive type should be used, then @val is used as key.
    To add custom xml-attributes on a list {'list': [4, 5, 6]}, you do this:

    .. python

        {'list': {
                    '@attrs': {'a':'b',
                                'c':'d',
                                },
                    '@val': [4, 5, 6],
                }
        }

    .. xml

        <list a="b" c="d">
            <item>4</item>
            <item>5</item>
            <item>6</item>
        </list>

    """

from __future__         import annotations
import datetime
import logging
import numbers
from collections.abc    import Callable, Sequence
from decimal            import Decimal
from fractions          import Fraction
from random             import SystemRandom
from typing             import Any, Union, cast

from defusedxml.minidom import parseString

PROLOG              = '<?xml version="1.0" encoding="UTF-8" ?>'
XPATH_FUNCTIONS_NS  = 'http://www.w3.org/2005/xpath-functions'

# ##############################################

# Create a safe random number generator

# Set up logging
LOG = logging.getLogger("dicttoxml")

def make_id(      element: str, start: int = 100000, end: int = 999999) -> str:
    """
    Generate a random ID for a given element

    Args:
        element (str): the element to generate an ID for
        start (int, optional): The lower bound for the random number. Defaults to 100000
        end   (int, optional): The upper bound for the random number. Defaults to 999999

    Returns:
        str: the generated ID
    """

    return '' + element + '_' + str(SystemRandom().randint(start, end))

def get_unique_id(element: str)                                         -> str:
    """
    Generate a unique ID for a given element

    Args:
        element (str): the element to generate an ID for

    Returns:
        str: the unique ID
    """
    ids: list[str]  = []
    while True:
        this_id:  str   = make_id(element)
        if  this_id not in ids:
            ids.append(this_id)
            return ids[-1]                  # last in the list

# ##############################################

ELEMENT = Union[
    str,
    int,
    float,
    bool,
    complex,
    Decimal,
    Fraction,
    numbers.Number,
    Sequence[Any],
    datetime.datetime,
    datetime.date,
    None,
    dict[str, Any],
]

def get_xml_type(val: ELEMENT)                          -> str:
    """
    Get the XML type of a given value

    Args:
        val (ELEMENT): the value to get the type of

    Returns:
        str: the XML type
    """

    if val is None:
            return_value =          "null"
    else:                          # val is not None:
        if  isinstance(val,          numbers.Number):
            return_value =          "number"
        if  isinstance(val,          dict):
            return_value =          "dict"
        if  isinstance(val,          Sequence):
            return_value =          "list"
        if  type(val).__name__ in  ("str", "unicode"):
            return_value =          "str"
        if  type(val).__name__ in  ("int", "long"):
            return_value =          "int"
        if  type(val).__name__ ==   "float":
            return_value =          "float"
        if  type(val).__name__ ==   "bool":
            return_value =          "bool"
        else:
            return_value =           type(val).__name__
    return  return_value

def escape_xml(s: str | int | float | numbers.Number)   -> str:
    """
    Escape a string for use in XML

    Args:
        s (str | numbers.Number): the string to escape

    Returns:
        str:                      the escaped string.
    """
    if isinstance(s, str):
        s = str(s)                      # avoid UnicodeDecodeError
        s = s.replace("&", "&amp;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
    return str(s)

def make_attrstring(attr: dict[str, Any])               -> str:
    """
    Create a string of XML attributes from a dictionary

    Args:
        attr (dict[str, Any]): the dictionary of attributes

    Returns:
        str:                   the string     of XML attributes
    """
    # TODO refactoring
    return " ".join([f'{k}="{escape_xml(v)}"' for k, v in attr.items()])

def distance(attributes: str)                           -> str:
    '''docstring'''
    if      attributes   == '':
            attr_distance = ''
    else:
            attr_distance = ' '
    return  attr_distance

def key_is_valid_xml(key: str)                          -> bool:
    """
    Check if a key is a valid XML name.

    Args:
        key (str): the key to check

    Returns:
        bool: True if the key is a valid XML name, False otherwise
    """

    test_xml =  PROLOG              \
                +  '<' + key + '>'  \
                +    'foo'          \
                + '</' + key + '>'
    try:
        parseString(test_xml)
        return True
    except Exception:  # minidom does not implement exceptions well
        return False

def make_valid_xml_name(key: str, attr: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Tests an XML name and fixes it if invalid"""

    # preparations:
    key = escape_xml(key)
    # nothing happens at escape_xml if attr is not a string,
    # we don't need to pass it to the method at all:
    # attr = escape_xml(attr)

    if  key_is_valid_xml(key):
        return key, attr

    if  isinstance(  key, int) or key.isdigit():
        return 'n' + key, attr          # prepend a lowercase n(?)

    if  key_is_valid_xml(key.replace(" ", "_")):
        return           key.replace(" ", "_"), attr

    # allow namespace prefixes + ignore @flat in key:
    if  key_is_valid_xml(key.replace(":", "").replace("@flat", "")):
        return key, attr

    # key is still invalid - move it into a name attribute:
    attr["name"] =  key
    key          = "key"
    return key, attr

# ##############################################

# TODO refactoring
def wrap_cdata(s: str | int | float | numbers.Number)               -> str:
    """Wraps a string into CDATA sections"""
    s = str(s).replace("]]>", "]]]]><![CDATA[>")
    return "<![CDATA[" + s +  "]]>"

# TODO reactivate this
# do not delete parent parameter
# def default_item_func(parent: str, text: str = "item")            -> str:
#     '''how to wrap array items'''
#     return text

# ##############################################

# XPath 3.1 json-to-xml conversion
def get_xpath31_tag_name(val: Any)                                  -> str:
    """
    Determine XPath 3.1 tag name by Python type
    See: https://www.w3.org/TR/xpath-functions-31/#func-json-to-xml
    Args:
        val: the value to get the tag name for
    """

    return_value = ""
    if              val is None:
        return_value = "null"
    #                   python types        tags
    python_to_tag = [   [bool,           "boolean", ],
                        [dict,           "map",     ],

                        [list,           "array",   ],
                        [Sequence,       "array",   ],

                        [str,            "string",  ],
                        [bytes,          "string",  ],
                        [bytearray,      "string",  ],

                        [int,            "number",  ],
                        [float,          "number",  ],
                        [numbers.Number, "number",  ],
                    ]
    for [python, tag] in python_to_tag:
        if  isinstance(val, python):
            return_value =  tag
            break
    if      return_value == "":
            return_value = "string"
    return  return_value

def convert_to_xpath31(  obj: Any, parent_key: str | None = None)   -> str:
    """
    Convert a Python object to XPath 3.1 json-to-xml format

    Args:
        obj:        the object to convert
        parent_key: the key from the parent dict (used for key attribute)

    Returns:
        str:        XML string in XPath 3.1 format
    """

    return_value        = ''
    if  parent_key is not None:
        key_attr        = 'key="' + escape_xml(parent_key) + '"'
    else:
        key_attr        = ''
    tag_name            = get_xpath31_tag_name(obj)
    # if  tag_name        ==    'null':
    #     return_value    =    '<null'       + ' ' + key_attr + '/>'

    #                 tags                    contents
    tag_to_conent = [   [ 'null',                   '',                                         ],
                        [ 'boolean',            str(obj).lower(),                               ],
                        [ 'number',                 obj,                                        ],
                        [ 'string',  escape_xml(str(obj)),                                      ],
                        [ 'map',     ''.join(convert_to_xpath31(v, k) for k, v in obj.items()), ],  # children
                        [ "array",   ''.join(convert_to_xpath31(item) for item in obj),         ],  # children
                ]
    for [tag, content] in tag_to_conent:
        if  tag_name    ==        tag:
            return_value = '<'  + tag      + ' ' + key_attr + '>'   \
                                + content                           \
                         + '</' + tag                       + '>'
            break
    if  return_value    == '':
        return_value     = '<'  + 'string' + ' ' + key_attr + '>'   \
                                +  escape_xml(str(obj))             \
                         + '</' + 'string'                  + '>'
    return return_value

# ##############################################

def is_primitive_type(val: Any)                                     -> bool:
    '''docstring'''
    xml_type        = get_xml_type(val)
    primitive_types = {"str", "int", "float", "bool", "number", "null"}
    return xml_type in primitive_types

def dict2xml_str(
    item:                   dict[str, Any],
    item_name:              str,
    attr_type:              bool,
    attr:                   dict[str, Any],
    cdata:                  bool,
    wrap_array_items:       bool,
    # array_items_wrap: Callable[[str], str],
    custom_array_item_wrap: str,
    parent_is_list:         bool,
    parent:                 str  = "",
    array_headers:          bool = False,
) -> str:

    """parse dict2xml"""

    ids: list[str]    = []         # initialize list of unique ids
    ", ".join(str(key) for key in item)         # ??
    if  attr_type:
        attr["type"]  = get_xml_type(item)
    val_attr: dict[str, str] = item.pop("@attrs", attr)  # update attr with custom @attr if exists
    subtree           = ""         # initialize subtree with default empty string
    if "@val"  in item:
        rawitem       = item["@val"]
    else:
        rawitem       = item
    if  is_primitive_type( rawitem):
        if   isinstance(   rawitem, dict):
             subtree  = escape_xml(str(rawitem))
        elif isinstance(   rawitem, str):
             subtree  = escape_xml(    rawitem)
    else:
        # we can not use convert_dict, because rawitem could be non-dict
             subtree  = convert(
                        rawitem, ids, attr_type, cdata, wrap_array_items, custom_array_item_wrap, item_name, array_headers=array_headers
                        )
    if parent_is_list and array_headers:
        if len(val_attr) > 0 and not wrap_array_items:
            attrstring   = make_attrstring(val_attr)
            return_value  = '<' + parent    + distance(attrstring) + attrstring + '>' + subtree + '</' + parent    + '>'
        else:
            return_value  = '<' + parent + '>'                                        + subtree + '</' + parent    + '>'
    elif item.get("@flat", False) or (parent_is_list and not wrap_array_items):
            return_value  =                                                             subtree
    else:
            attrstring   = make_attrstring(val_attr)
            return_value  = '<' + item_name + distance(attrstring) + attrstring + '>' + subtree + '</' + item_name + '>'
    return  return_value

def list2xml_str(
    item:                   Sequence[Any],
    item_name:              str,
    attr_type:              bool,
    attr:                   dict[str, Any],
    cdata:                  bool,
    wrap_array_items:       bool,
    # array_items_wrap: Callable[[str], str],
    custom_array_item_wrap: str,
    array_headers:          bool = False,
) -> str:
    
    '''docstring'''

    ids:  list[str]  = []  # initialize list of unique ids
    flat:      bool
    subtree:  str
    if  attr_type:
        attr["type"] = get_xml_type(item)
    if  item_name.endswith("@flat"):
        item_name = item_name[0:-5]
        flat      = True
    else:
        flat      = False
    subtree = ""           # Initialize subtree with default empty string
    subtree = convert_list(
        items=item,
        ids=ids,
        attr_type=attr_type,
        cdata=cdata,
        parent=item_name,
        wrap_array_items=wrap_array_items,
        # array_items_wrap=array_items_wrap,
        custom_array_item_wrap = custom_array_item_wrap,
        array_headers=array_headers
    )
    if flat             \
    or array_headers    \
    or (len(item) > 0 and is_primitive_type(item[0]) and not wrap_array_items):
        return_value = subtree
    else:
        attrstring  = make_attrstring(attr)
        return_value = '<'  + item_name + distance(attrstring) + attrstring  + '>'   \
                           + subtree                                                \
                    + '</' + item_name                                      + '>'
    return return_value

# ##############################################

def convert(
    obj:                    ELEMENT,
    ids:                    Any,
    attr_type:              bool,
    # array_items_wrap:       Callable[[str], str],
    cdata:                  bool,
    wrap_array_items:       bool,
    custom_array_item_wrap: str,
    parent:                 str     =   "root",
    array_headers:          bool    =    False,
) -> str:
    """Routes the elements of an object to the right function
    to convert them based on their data type"""

    # item_name = array_items_wrap(parent)
    item_name = custom_array_item_wrap

    # since bool is also a subtype of number.Number and int,
    # the check for bool never comes
    # and hence we get wrong value for the xml type bool here;
    # we just change order and check for bool first,
    # because no other type than bool can be true for bool check
    if   isinstance(obj, bool):
        return   convert_bool(  key=item_name, val=obj,             attr_type=attr_type,          cdata=cdata, )

    elif isinstance(obj, numbers.Number):
        return   convert_number(key=item_name, val=obj,             attr_type=attr_type, attr={}, cdata=cdata, )

    elif isinstance(obj, str):
        return   convert_number(key=item_name, val=obj,             attr_type=attr_type, attr={}, cdata=cdata, )

    elif isinstance(obj, (datetime.datetime, datetime.date))  and hasattr(obj, "isoformat") :
        return   convert_number(key=item_name, val=obj.isoformat(), attr_type=attr_type, attr={}, cdata=cdata, )

    elif obj is          None:
        return   convert_none(  key=item_name,                      attr_type=attr_type,          cdata=cdata)

    elif isinstance(obj, dict):
        return   convert_dict(cast("dict[str, Any]", obj), ids, attr_type, cdata, parent, wrap_array_items, custom_array_item_wrap, array_headers=array_headers)

    elif isinstance(obj, Sequence):
        return   convert_list(                        obj, ids, attr_type, cdata, parent, wrap_array_items, custom_array_item_wrap, array_headers=array_headers)

    else:
        raise TypeError('Unsupported data type: ' + str(obj) + ' (' + type(obj).__name__ + ')' )

def convert_dict(
    obj:                        dict[str, Any],
    ids:                        list[str],
    attr_type:                  bool,
    cdata:                      bool,
    parent:                     str,
    wrap_array_items:           bool,
    # array_items_wrap: Callable[[str], str],
    custom_array_item_wrap:     str,
    array_headers:              bool = False
) -> str:
    """Converts a dict into an XML string"""

    output: list[str] = []
    attr:   dict[str, str]
    addline           = output.append
    for key, val in obj.items():
        if  ids:
             attr     = {"id": get_unique_id(parent)}
        else:
             attr     = {}
        key, attr     = make_valid_xml_name(key, attr)

        # since bool is also a subtype of number.Number and int, the check for bool
        # never comes and hence we get wrong value for the xml type bool
        # here, we just change order and check for bool first, because no other
        # type other than bool can be true for bool check
        if   isinstance(val, bool):
            addline(
                convert_bool(
                    key,
                    val,
                    attr_type,
                    attr,
                    cdata,
                )
            )
        elif isinstance(val, (numbers.Number, str)):
            addline(
                convert_number(
                    key=key,
                    val=val,
                    attr_type=attr_type,
                    attr=attr,
                    cdata=cdata,
                )
            )
        elif hasattr(val, "isoformat"):  # datetime
            addline(
                convert_number(
                    key=key,
                    val=val.isoformat(),            # difference
                    attr_type=attr_type,
                    attr=attr,
                    cdata=cdata,
                )
            )
        elif isinstance(val, dict):
            addline(
                dict2xml_str(
                    val,
                    key,
                    attr_type,
                    attr,
                    cdata,
                    wrap_array_items,               # difference
                    custom_array_item_wrap,         # difference
                    False,      # parent_is_list?   # difference
                    # no line for parent?
                    array_headers=array_headers,    # difference
                )
            )
        elif isinstance(val, Sequence):
            addline(
                list2xml_str(
                    item=val,
                    item_name=key,
                    attr_type=attr_type,
                    attr=attr,
                    cdata=cdata,
                    wrap_array_items=wrap_array_items,
                    custom_array_item_wrap=custom_array_item_wrap,
                    array_headers=array_headers,
                )
            )
        elif not val:
            addline(
                convert_none(
                    key,
                    attr_type,
                    attr,
                    cdata,
                )
            )
        else:
            raise TypeError('Unsupported data type: ' + val + '(' + type(val).__name__ + ')')
    return ''.join(output)

def convert_list(
    items:                  Sequence[Any],
    ids:                    list[str] | None,
    attr_type:              bool,
    cdata:                  bool,
    parent:                 str,
    wrap_array_items:       bool,
    # array_items_wrap: Callable
    custom_array_item_wrap: str,
    array_headers:          bool = False,
) -> str:
    """Converts a list into an XML string"""

    output: list[str] = []
    attr:   dict[str, str]
    addline           = output.append
    # orig. was: item_name = array_items_wrap(parent)
    item_name         = custom_array_item_wrap  # Is item_name still relevant if wrap_array_items is false
    if  item_name.endswith("@flat"):
        item_name     = item_name[:-5]          # remove "@flat"
    if  ids:
        this_id       = get_unique_id(parent)
    else:
        this_id       = None
    for i, item in enumerate(items):
        if  ids:
            attr = {'id': str(this_id) + '_' + str(i + 1)}
        else:
            attr = {}
        if item is None:
                addline(
                    convert_none(
                        item_name,
                        # difference: no item
                        attr_type,
                        attr,
                        cdata
                    )
                )
        elif isinstance(item, bool):
                addline(
                    convert_bool(
                        item_name,
                        item,
                        attr_type,
                        attr,
                        cdata
                    )
                )
        elif isinstance(item, (numbers.Number, str)):
            if  wrap_array_items:
                addline(
                    convert_number(
                        key=item_name,
                        val=item,
                        attr_type=attr_type,
                        attr=attr,
                        cdata=cdata,
                    )
                )
            else:   # not wrap_array_items
                addline(
                    convert_number(
                        key=parent,             # difference
                        val=item,
                        attr_type=attr_type,
                        attr=attr,
                        cdata=cdata,
                    )
                )
        elif hasattr(item, "isoformat"):  # datetime
                addline(
                    convert_number(
                        key=item_name,
                        val=item.isoformat(),   # difference
                        attr_type=attr_type,
                        attr=attr,
                        cdata=cdata,
                    )
                )
        elif isinstance(item, dict):
                addline(
                    dict2xml_str(
                        item=item,
                        item_name=item_name,
                        attr_type=attr_type,
                        attr=attr,
                        cdata=cdata,
                        wrap_array_items=wrap_array_items,
                        # array_items_wrap=array_items_wrap,
                        custom_array_item_wrap=custom_array_item_wrap,
                        parent_is_list=True,                # difference
                        parent=parent,                      # difference
                        array_headers=array_headers
                    )
                )
        elif isinstance(item, Sequence):
                addline(
                    list2xml_str(
                        item=item,
                        item_name=item_name,
                        attr_type=attr_type,
                        attr=attr,
                        cdata=cdata,
                        wrap_array_items=wrap_array_items,
                        # array_items_wrap=array_items_wrap,
                        custom_array_item_wrap=custom_array_item_wrap,
                        array_headers=array_headers
                    )
                )
        else:
            raise TypeError('Unsupported data type: ' + item + '(' + type(item).__name__ + ')')
    return ''.join(output)

# TODO make a general fct out of these ("convert a value into an XML element"):
def convert_number(
    key:        str,
    val:        int | float | numbers.Number | datetime.datetime | datetime.date | str,
    attr_type:  bool,
    attr:       dict[str, Any] | None = None,
    cdata:      bool                  = False,
) -> str:
    """Converts a number, datetime, or string into an XML element"""

    if  attr is None:
        attr  = {}
    key, attr = make_valid_xml_name(key, attr)
    if  isinstance(val, (datetime.datetime, datetime.date)) and hasattr(val, "isoformat"):
        val   = val.isoformat()
    if  attr_type:
        attr["type"]    = get_xml_type(val)
    attrstring          = make_attrstring(attr)
    if  cdata:
        formatted_val   = wrap_cdata(val)
    else:
        formatted_val   = escape_xml(val)
    return '<'  + key + distance(attrstring) + attrstring + '>'   \
                + formatted_val                                   \
        +  '</' + key                                     + '>'

def convert_bool(
    key:        str,
    val:        bool,
    attr_type:  bool,
    attr:       dict[str, Any] | None   = None,
    cdata:      bool                    = False               # is used in fct calls
) -> str:
    """Converts a boolean into an XML element"""

    if  attr is None:
        attr = {}
    key, attr = make_valid_xml_name(key, attr)
    if  attr_type:
        attr["type"] = get_xml_type(val)      # "bool"
    attrstring       = make_attrstring(attr)
    return '<'  + key + distance(attrstring) + attrstring + '>'   \
                + str(val).lower()                                \
         + '</' + key                                     + '>'

def convert_none(
    key:        str,
    attr_type:  bool,
    attr:       dict[str, Any] | None   = None,
    cdata:      bool                    = False               # is used in fct calls
) -> str:
    """Converts a null value into an XML element"""

    if  attr is None:
        attr = {}
    key, attr = make_valid_xml_name(key, attr)
    if  attr_type:
        attr["type"]  = get_xml_type(None)    # "null"
    attrstring        = make_attrstring(attr)
    return '<'  + key + distance(attrstring) + attrstring + '>'   \
         + '</' + key                                     + '>'

# ##############################################

def dicttoxml(
    obj:            ELEMENT,
    xpath_format:   bool                    = False,                # default is False

    use_root:       bool                    = True,                 # default is True;  wrap the output into an XML root element
    custom_root:    str                     = "root",               # default is "root"

    wrap_array_items:   bool                = True,                 # default is True;  wrap each array item into a tag
    # array_items_wrap:   Callable[[str], str]= default_item_func,    # default is default_item_func; how to generate the tag for each array item; TODO does NOT come from json2xml
    custom_array_item_wrap: str             = 'node',

    array_headers:  bool                    = False,                # default is False; wrap each array item into the outer header (see also wrap_array_items)
    attr_type:      bool                    = True,                 # default is True;  display data type
    cdata:          bool                    = False,                # default is False; wrap string values into CDATA sections
    ids:            list[int]      | None   = None,                 # default is None / [];  elements get unique ids
    xml_namespaces: dict[str, Any] | None   = None,                 # default is None / {}
    prolog:         str                     = PROLOG
) -> bytes:
    '''docstring: see top of file'''
    if  xpath_format:
        xml_content     = convert_to_xpath31(obj)
        xmlns           = 'xmlns="' + XPATH_FUNCTIONS_NS + '"'
        if  xml_content.startswith(           '<array>'):
            part2       = xml_content.replace('<array>',
                                              '<array ' + xmlns + '>', 1)
        elif xml_content.startswith(          '<map>'):
            part2       = xml_content.replace('<map>',
                                              '<map '   + xmlns + '>', 1)
        else:
            part2       =                     '<map '   + xmlns + '>'   \
                                                        + xml_content   \
                                            + '</map>'
        output          = prolog + part2
    else:                       # not xpath_format
        output          = ''
        namespace_str   = ''
        if  xml_namespaces is None:
            xml_namespaces = {}
        for     prefix in xml_namespaces:
            if  prefix == 'xsi':
                for schema_att in xml_namespaces[prefix]:
                    if schema_att == 'schemaInstance':
                        ns = xml_namespaces[prefix]['schemaInstance']
                        namespace_str += f' xmlns:{prefix}="{ns}"'
                    elif schema_att == 'schemaLocation':
                        ns = xml_namespaces[prefix][schema_att]
                        namespace_str += f' xsi:{schema_att}="{ns}"'
            elif prefix == 'xmlns':
                # xmns needs no prefix
                ns              = xml_namespaces[prefix]
                namespace_str += f' xmlns="{ns}"'
            else:
                ns              = xml_namespaces[prefix]
                namespace_str += f' xmlns:{prefix}="{ns}"'
        if  use_root:
            output_elem = convert(
                obj, ids, attr_type, cdata, wrap_array_items, custom_array_item_wrap, parent=custom_root, array_headers=array_headers)
            output      = prolog                                            \
                        + '<'   + custom_root + ' ' + namespace_str + '>'   \
                                + output_elem                               \
                        + '</'  + custom_root                       + '>'
        else:                   # not use_root
            custom_root = ''
            output_elem = convert(
                obj, ids, attr_type, cdata, wrap_array_items, custom_array_item_wrap, parent=custom_root, array_headers=array_headers)
            output      = output_elem       # no prolog here, since it needs custom root
    return "".join(output).encode("utf-8")
