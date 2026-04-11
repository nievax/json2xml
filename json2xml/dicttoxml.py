"""
    function dicttoxml (see below) converts a python object into XML.

    :param dict obj:

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
        default is []

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

            <root xmlns:flex="http://www.w3.org/flex/flexBase"
                  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

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
    ids: list[str]      = []
    while True:
        this_id:  str   = make_id(element)
        if  this_id not in ids:
            ids.append(this_id)
            return     this_id

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

def make_bundle(attr_type:                   bool               = True,
                cdata:                       bool               = False,
                custom_array_item_wrap:      str                = '',
                array_headers:               bool               = False,
                attr:                   dict[str, Any] | None   = None,
                )                                                   -> dict[str, str | bool]:
    '''docstring'''
    if  attr is None:
        attr  = {}
    bundle: dict[str, Any] = {  'attr_type':                attr_type,
                                'cdata':                    cdata,
                                'custom_array_item_wrap':   custom_array_item_wrap,
                                'array_headers':            array_headers,
                                'attr':                     attr,
    }
    return bundle

def get_xml_type(val: ELEMENT)                                      -> str:
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

def escape_xml(s: str | int | float | numbers.Number)               -> str:
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

# TODO refactoring
def make_attrstring(attr: dict[str, Any])                           -> str:
    """
    Create a string of XML attributes from a dictionary

    Args:
        attr (dict[str, Any]): the dictionary of attributes

    Returns:
        str:                   the string     of XML attributes
    """
    return " ".join([f'{k}="{escape_xml(v)}"' for k, v in attr.items()])

def distance(attributes: str)                                       -> str:
    '''docstring'''
    if      attributes   == '':
            attr_distance = ''
    else:
            attr_distance = ' '
    return  attr_distance

def key_is_valid_xml(   key: str)                                   -> bool:
    """
    Check if a key is a valid XML name.

    Args:
        key (str): the key to check

    Returns:
        bool: True if the key is a valid XML name, False otherwise
    """

    test_xml =  PROLOG + make_tag(key, '', 'foo')
    try:
        parseString(test_xml)
        return True
    except Exception:  # minidom does not implement exceptions well
        return False

# TODO return / break logic
def make_valid_xml_name(key: str, attr: dict[str, Any])             -> tuple[str, dict[str, Any]]:
    """Tests an XML name and fixes it if invalid"""

    # preparations:
    key = escape_xml(key)
    # nothing happens at escape_xml if attr is not a string,
    # we don't need to pass it to the method at all:
    # attr = escape_xml(attr)

    if  key_is_valid_xml(key):
        return           key, attr

    if  isinstance(      key, int) or key.isdigit():
        return 'n'     + key, attr          # prepend a lowercase n(?)

    if  key_is_valid_xml(key.replace(" ", "_")):
        return           key.replace(" ", "_"), attr

    # allow namespace prefixes + ignore @flat in key:
    if  key_is_valid_xml(key.replace(":", "").replace("@flat", "")):
        return           key, attr

    # key is still invalid - move it into a name attribute:
    key          = "key"
    attr["name"] =  key
    return          key, attr

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

def open_tag( tag_name: str, attrs: str = '')                       -> str:
    '''docstring'''
    return                    '<'     + tag_name + distance(attrs) + attrs + '>'

def close_tag(tag_name: str)                                        -> str:
    '''docstring'''
    return                    '</'    + tag_name                           + '>'

def make_tag( tag_name: str, attrs: str = '', content: str = '')    -> str:
    '''docstring'''
    if  content != '':
        return_value: str   = open_tag( tag_name, attrs)    \
                            +               content         \
                            + close_tag(tag_name)
    else:   # content == ''
        return_value        = '<'     + tag_name + distance(attrs) + attrs + '/>'
    return return_value

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
    tag_to_content = [  [ 'null',                   '',                                         ],
                        [ 'boolean',            str(obj).lower(),                               ],
                        [ 'number',                 obj,                                        ],
                        [ 'string',  escape_xml(str(obj)),                                      ],
                        [ 'map',     ''.join(convert_to_xpath31(v, k) for k, v in obj.items()), ],  # children
                        [ "array",   ''.join(convert_to_xpath31(item) for item in obj),         ],  # children
                ]
    for [tag, content]   in tag_to_content:
        if  tag_name     ==            tag:
            return_value  =  make_tag( tag,      key_attr, content)
            break
    if      return_value == '':
            return_value  =  make_tag( 'string', key_attr, escape_xml(str(obj)) )
    return  return_value

# ##############################################

def is_primitive_type(   val: Any)                                  -> bool:
    '''docstring'''
    xml_type        = get_xml_type(val)
    primitive_types = {"str", "int", "float", "bool", "number", "null"}
    return xml_type in primitive_types

# TODO understand
def dict2xml_str(
    bundle:                 dict[str, Any],
    item:                   dict[str, Any],
    item_name:                   str,
    parent_is_list:              bool,
    parent:                      str        = "",
    # # wrap_array_items:       bool,
    # # array_items_wrap: Callable[[str], str],
)                                                                   -> str:
    """parse dict2xml"""
    return_value:                str        = ''
    attr_type:                   bool       = bundle['attr_type']
    attr:                   dict[str, Any]  = bundle['attr']
    cdata:                       bool       = bundle['cdata']
    custom_array_item_wrap:      str        = bundle['custom_array_item_wrap']
    array_headers:               bool       = bundle['array_headers']
    ids:                    list[str]       = []
    if  attr_type:
        attr["type"]      = get_xml_type(item)
    val_attr: dict[str, str] = item.pop("@attrs", attr)  # update attr with custom @attr if exists
    subtree               = ""         # initialize subtree with default empty string
    if "@val"  in item:
        rawitem           = item["@val"]
    else:
        rawitem           = item
    if  is_primitive_type( rawitem):
        if   isinstance(   rawitem, dict):
             subtree      = escape_xml( str(rawitem))
        elif isinstance(   rawitem, str):
             subtree      = escape_xml(     rawitem)
    else:
        # we can not use convert_dict, because rawitem could be non-dict
             subtree      = convert(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers),
                                    rawitem,
                                    ids,
                                    item_name,
                            )
    if parent_is_list and array_headers:
        if len(val_attr)  > 0                        and     custom_array_item_wrap != '':
            attrstring    = make_attrstring(val_attr)
            return_value  = make_tag( parent,    attrstring, subtree)
        else:
            return_value  = make_tag( parent,    '',         subtree)
    elif item.get("@flat", False) or (parent_is_list and     custom_array_item_wrap != ''):
            return_value  =                                  subtree
    else:
            attrstring    = make_attrstring(val_attr)
            return_value  = make_tag( item_name, attrstring, subtree)
    return  return_value

def list2xml_str(
    bundle:                 dict[str, Any],
    item:                   Sequence[ Any],
    item_name:                   str,
    # wrap_array_items:       bool,
    # array_items_wrap: Callable[[str], str],
)                                                                   -> str:
    '''parse list2xml'''
    return_value:                str        = ''
    attr_type:                   bool       = bundle['attr_type']
    attr:                   dict[str, Any]  = bundle['attr']
    cdata:                       bool       = bundle['cdata']
    custom_array_item_wrap:      str        = bundle['custom_array_item_wrap']
    array_headers:               bool       = bundle['array_headers']
    ids:                    list[str]       = []
    flat:                        bool
    subtree:                     str
    if  attr_type:
        attr["type"] = get_xml_type(item)
    if  item_name.endswith("@flat"):
        item_name = item_name[0:-5]
        flat      = True
    else:
        flat      = False
    subtree = ""           # Initialize subtree with default empty string
    subtree = convert_list(
        make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers),
        item,
        ids,
        item_name,
        # wrap_array_items=wrap_array_items,
        # array_items_wrap=array_items_wrap,
    )
    if flat             \
    or array_headers    \
    or (len(item) > 0 and is_primitive_type(item[0]) and custom_array_item_wrap != ''):
        return_value = subtree
    else:
        attrstring   = make_attrstring(attr)
        return_value = make_tag(item_name, attrstring, subtree)
    return return_value

# ##############################################

# TODO understand
def convert(
    bundle:                 dict[str, Any],
    obj:                    ELEMENT,
    ids:                         Any,        # default is list[str]
    # array_items_wrap:       Callable[[str], str],
    # wrap_array_items:       bool,
    parent:                     str     = "root",        # TODO or better use custom_root?
) -> str:
    """Routes the elements of an object to the right function
    to convert them based on their data type"""
    return_name:                str     = ""
    attr_type:                  bool    = bundle['attr_type']
    cdata:                      bool    = bundle['cdata']
    custom_array_item_wrap:     str     = bundle['custom_array_item_wrap']
    array_headers:              bool    = bundle['array_headers']
    # item_name = array_items_wrap(parent)
    item_name = custom_array_item_wrap

    # since bool is also a subtype of number.Number and int,
    # the check for bool never comes
    # and hence we get wrong value for the xml type bool here;
    # we just change order and check for bool first,
    # because no other type than bool can be true for bool check
    match obj:
        case bool():
            return_name = convert_bool(  item_name, obj,             attr_type,     cdata=cdata)
        case numbers.Number()     | str() :
            return_name = convert_number(item_name, obj,             attr_type, {}, cdata)
        case (datetime.datetime() | datetime.date()) if hasattr(obj, "isoformat") :
            return_name = convert_number(item_name, obj.isoformat(), attr_type, {}, cdata)
        case None:
            return_name = convert_none(  item_name,                  attr_type,     cdata=cdata)
        case dict():
            return_name = convert_dict(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers),
                              cast("dict[str, Any]", obj), ids, parent)
        case Sequence():
            return_name =convert_list(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers),
                              obj,                         ids, parent)
        case _:
            raise TypeError('Unsupported data type: ' + str(obj) + ' (' + type(obj).__name__ + ')' )
    return  return_name

def convert_dict(
    bundle:                 dict[str, Any],
    obj:                    dict[str, Any],
    ids:                    list[str],
    parent:                      str,
    # wrap_array_items:           bool,
    # array_items_wrap: Callable[[str], str],
) -> str:
    """Converts a dict into an XML string"""
    output:                 list[str]       = []                    # or str?
    attr_type:                   bool       = bundle['attr_type']
    cdata:                       bool       = bundle['cdata']
    custom_array_item_wrap:      str        = bundle['custom_array_item_wrap']
    array_headers:               bool       = bundle['array_headers']
    attr:                   dict[str, str]
    for key, val in obj.items():
        if   ids:
             attr     = {"id": get_unique_id(parent)}
        else:
             attr     = {}
        key, attr     = make_valid_xml_name(key, attr)

        # since bool is also a subtype of number.Number and int, the check for bool
        # never comes and hence we get wrong value for the xml type bool
        # here, we just change order and check for bool first, because no other
        # type other than bool can be true for bool check
        match val:
            case bool():
                output.append(convert_bool(  key, val,              attr_type, attr, cdata, ) )
            case numbers.Number() | str():
                output.append(convert_number(key, val,              attr_type, attr, cdata, ) )
            case (datetime.datetime() | datetime.date()) if hasattr(val, "isoformat"):
                output.append(convert_number(key, val.isoformat(),  attr_type, attr, cdata, ) )
            case dict():
                output.append(dict2xml_str(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers, attr),
                                                                    val, key, False,        ) )
            case Sequence():
                output.append(list2xml_str(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers, attr),
                                                                    val, key,               ) )
                    # wrap_array_items=wrap_array_items,
            case None:
                output.append(convert_none(  key,                   attr_type, attr, cdata, ) )
            case _:
                raise TypeError('Unsupported data type: ' + val + '(' + type(val).__name__ + ')')
    return ''.join(output)

def convert_list(
    bundle:                 dict[str, Any],
    items:                  Sequence[ Any],
    ids:                    list[str],
    parent:                      str,
    # wrap_array_items:       bool,
    # array_items_wrap: Callable
) -> str:
    """Converts a list into an XML string"""
    output:                 list[str]       = []                    # or str?
    attr_type:                   bool       = bundle['attr_type']
    cdata:                       bool       = bundle['cdata']
    custom_array_item_wrap:      str        = bundle['custom_array_item_wrap']
    array_headers:               bool       = bundle['array_headers']
    attr:                   dict[str, str]
    # TODO orig. was: item_name = array_items_wrap(parent)
    item_name           = custom_array_item_wrap  # Is item_name still relevant if wrap_array_items is false
    if  item_name.endswith("@flat"):
        item_name       = item_name[:-5]          # remove "@flat"
    for i, item in enumerate(items, start=1):
        if  ids:
            attr        = {'id': str(get_unique_id(parent)) + '_' + str(i)}
        else:
            attr        = {}
        match item:
            case None:
                output.append(convert_none(  item_name,                   attr_type, attr, cdata, ))
            case bool():
                output.append(convert_bool(  item_name, item,             attr_type, attr, cdata, ))
            case (numbers.Number() | str()) if custom_array_item_wrap != '':
                output.append(convert_number(item_name, item,             attr_type, attr, cdata, ))
            case (numbers.Number() | str()) if custom_array_item_wrap == '':
                output.append(convert_number(parent,    item,             attr_type, attr, cdata, ))
            case (datetime.date() | datetime.datetime()) if hasattr(item, "isoformat"):
                output.append(convert_number(item_name, item.isoformat(), attr_type, attr, cdata, ))
            case dict():
                output.append(dict2xml_str(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers, attr),
                                                        item, item_name, True, parent,            ))
                        # wrap_array_items=wrap_array_items,
                        # array_items_wrap=array_items_wrap,
            case Sequence():
                output.append(list2xml_str(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers, attr),
                                                        item, item_name,                          ))
                        # wrap_array_items=wrap_array_items,
                        # array_items_wrap=array_items_wrap,
            case _:
                raise TypeError('Unsupported data type: ' + item + '(' + type(item).__name__ + ')')
    return ''.join(output)

# TODO make a general fct out of these ("convert a value into an XML element"):
def convert_number(
    key:             str,
    val:        int | float | numbers.Number | datetime.datetime | datetime.date | str,
    attr_type:       bool,
    attr:       dict[str, Any] | None = None,
    cdata:           bool             = False,
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
    return make_tag(key, attrstring, formatted_val)

def convert_bool(
    key:             str,
    val:             bool,
    attr_type:       bool,
    attr:       dict[str, Any] | None   = None,
    cdata:           bool               = False               # is used in fct calls
) -> str:
    """Converts a boolean into an XML element"""
    if  attr        is None:
        attr         = {}
    key, attr        = make_valid_xml_name(key, attr)
    if  attr_type:
        attr["type"] = get_xml_type(val)      # "bool"
    attrstring       = make_attrstring(attr)
    return make_tag(key,    attrstring, str(val).lower())

def convert_none(
    key:             str,
    attr_type:       bool,
    attr:       dict[str, Any] | None   = None,
    cdata:           bool               = False               # is used in fct calls
)                                                                   -> str:
    """Converts a null value into an XML element"""
    if  attr         is None:
        attr          = {}
    key, attr         = make_valid_xml_name(key, attr)
    if  attr_type:
        attr["type"]  = get_xml_type(None)    # "null"
    attrstring        = make_attrstring(attr)
    return make_tag(key,     attrstring)

# ##############################################

def set_xpath(obj)                                                  -> str:
    '''set output for xpath'''
    xml_content     = convert_to_xpath31(obj)
    xmlns           = 'xmlns="' + XPATH_FUNCTIONS_NS + '"'
    if                xml_content.startswith(         '<array>'):
        part2       = xml_content.replace(            '<array>',
                                             open_tag( 'array', xmlns), 1)
    elif              xml_content.startswith(         '<map>'):
        part2       = xml_content.replace(            '<map>',
                                             open_tag( 'map',   xmlns), 1)
    else:
        part2       =                        make_tag( 'map',   xmlns, xml_content)
    return PROLOG   + part2

def set_namespace_str(xml_namespaces: dict[str, Any])               -> str:
    '''set namespace string from xml_namespaces'''
    namespace_str                                    = ''
    for     prefix in xml_namespaces:
        if  prefix ==  'xmlns':
                    namespace_str                   += ' ' + 'xmlns'                           + '="' + xml_namespaces[prefix]             + '"'
        elif prefix == 'xsi':
            for     schema_att in xml_namespaces[prefix]:
                if  schema_att ==              'schemaInstance':
                    namespace_str                   += ' ' + 'xmlns' + ':'  + 'xsi'            + '="' + xml_namespaces[prefix][schema_att] + '"'
                elif schema_att in [           'schemaLocation',
                                    'noNamespaceSchemaLocation', ]:
                    namespace_str                   += ' ' + 'xsi'   + ':'  +  schema_att      + '="' + xml_namespaces[prefix][schema_att] + '"'
        else:
                    namespace_str                   += ' ' + 'xmlns' + ':'  +  prefix          + '="' + xml_namespaces[prefix]             + '"'
    return          namespace_str

def dicttoxml(
    obj:            ELEMENT,
    bundle:         dict[str, Any]          = {
                                'attr_type':                True,   # display data type
                                'cdata':                    False,  # wrap string values   into CDATA sections
                                'custom_array_item_wrap':   'node',
                                'array_headers':            False,  # wrap each array item into the outer header (see also wrap_array_items) 
    },
    xpath_format:        bool               = False,                # default is False
    custom_root:         str                = "root",               # default is "root"; TODO or better use custom_root?
    # wrap_array_items:   bool                = True,               # default is True;  wrap each array item into a tag
    # array_items_wrap:   Callable[[str], str]= default_item_func,  # default is default_item_func; how to generate the tag for each array item; TODO does NOT come from json2xml
    only_read_folder:    str                = "",
    ids:            list[int]      | None   = None,                 # default is None;  elements get unique ids; default is list[str]
    xml_namespaces: dict[str, Any] | None   = None,                 # default is None
)                                                                   -> bytes:
    '''docstring: see top of file'''
    output                                  = ''
    attr_type:              bool            = bundle['attr_type']
    cdata:                  bool            = bundle['cdata']
    custom_array_item_wrap: str             = bundle['custom_array_item_wrap']
    array_headers:          bool            = bundle['array_headers']
    if  xml_namespaces     is None:
        xml_namespaces      = {}
    if  ids                is None:
        ids                 = []
    if  xpath_format:
        output              = set_xpath(obj)
    else:
        namespace_str       = set_namespace_str(xml_namespaces)
        if  custom_root == '':                    # TODO instead of this, integrate it into fct as default value:
            if  only_read_folder:       #      != ''
                custom_root = only_read_folder
            else:       #  if only_read_folder == ''
                custom_root = 'root'    # custom root is needed in every case ...
                                        # ... to prevent ExpatError / InvalidDataError in json2xml.py / fct to_xml()
        output_elem         = convert(make_bundle(attr_type, cdata, custom_array_item_wrap, array_headers),
                                      obj,
                                      ids,
                                      custom_root)
        output              = PROLOG + make_tag(custom_root, namespace_str, output_elem)
    return ''.join(output).encode('utf-8')
