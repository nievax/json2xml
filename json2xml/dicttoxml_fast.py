"""
Fast dicttoxml implementation with automatic backend selection.

This module provides a dicttoxml function
that automatically uses the high-performance Rust implementation when available,
falling back to the pure Python implementation otherwise.

Usage:
    from json2xml.dicttoxml_fast import dicttoxml

    # Automatically uses fastest available backend
    xml_bytes = dicttoxml({"name": "John", "age": 30})
"""

from __future__         import annotations
import logging
from collections.abc    import Callable
from typing             import Any
# Import the pure Python implementation as fallback:
from json2xml           import dicttoxml    as _py_dicttoxml  # noqa: E402

LOG             = logging.getLogger("dicttoxml_fast")

# Try to import the Rust implementation
_USE_RUST       = False
_rust_dicttoxml = None

try:
    from json2xml_rs import dicttoxml       as _rust_dicttoxml  # type: ignore[import-not-found]  # pragma: no cover
    from json2xml_rs import escape_xml_py   as rust_escape_xml  # type: ignore[import-not-found]  # pragma: no cover
    from json2xml_rs import wrap_cdata_py   as rust_wrap_cdata  # type: ignore[import-not-found]  # pragma: no cover
    _USE_RUST       = True                          # pragma: no cover
    LOG.debug("Using Rust backend for dicttoxml")   # pragma: no cover
except ImportError:                                 # pragma: no cover
    LOG.debug("Rust backend not available, using pure Python")
    rust_escape_xml = None
    rust_wrap_cdata = None


def is_rust_available() -> bool:
    """Check if the Rust backend is available."""
    return _USE_RUST


def get_backend() -> str:
    """Return the name of the current backend ('rust' or 'python')."""
    return "rust" if _USE_RUST else "python"


def dicttoxml(
    obj:                Any,
    xpath_format:       bool                        = False,
    use_root:           bool                        = True,
    custom_root:        str                         = "root",
    wrap_array_items:   bool                        = True,
    array_items_wrap:          Callable[[str], str] | None = None,     # TODO
    list_headers:       bool                        = False,
    attr_type:          bool                        = True,
    cdata:              bool                        = False,
    ids:                list[int] | None            = None,
    xml_namespaces:     dict[str, Any] | None       = None,
) -> bytes:
    """
    Convert a Python dict or list to XML

    This function automatically uses the Rust backend when available for maximum performance,
    falling back to pure Python for unsupported features.

    Args:
        obj:                the Python object to convert (dict or list)
        use_root:           include XML declaration and root element    (default: True)
        custom_root:        name of the root element                    (default: "root")
        attr_type:          include type attributes on elements         (default: True)
        cdata:              wrap string values in CDATA sections        (default: False)
        list_headers:       repeat parent tag for each list item        (default: False)
        wrap_array_items:   wrap list items in <item> tags              (default: True)
        array_items_wrap:   custom function for item names      (not supported in Rust)
        xpath_format:       use XPath 3.1 format                (not supported in Rust)
        xml_namespaces:     XML namespace definitions           (not supported in Rust)
        ids:                generate unique IDs for elements    (not supported in Rust)

    Returns:
        UTF-8 encoded XML as bytes
    """
    # Features that require Python fallback
    needs_python = (
        ids                 is not None
        or array_items_wrap is not None
        or xml_namespaces
        or xpath_format
    )

    # Check for special dict keys that require Python
    if not needs_python and isinstance(     obj, dict):
           needs_python = _has_special_keys(obj)

    if not needs_python and _USE_RUST and _rust_dicttoxml is not None:  # pragma: no cover
        # Use fast Rust implementation
        return _rust_dicttoxml(
            obj,
            use_root=use_root,
            custom_root=custom_root,
            wrap_array_items=wrap_array_items,
            list_headers=list_headers,
            attr_type=attr_type,
            cdata=cdata,
        )
    else:
        # Fall back to pure Python
        return _py_dicttoxml.dicttoxml(
            obj,
            xpath_format=xpath_format,
            use_root=use_root,
            custom_root=custom_root,
            wrap_array_items=wrap_array_items,
            array_items_wrap=array_items_wrap or _py_dicttoxml.default_item_func,
            list_headers=list_headers,
            attr_type=attr_type,
            cdata=cdata,
            ids=ids,
            xml_namespaces=xml_namespaces or {},
        )


def _has_special_keys(obj: Any) -> bool:
    """Check if a dict contains special keys that require Python processing."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if  isinstance(key, str) and (
                key.startswith("@")  or key.endswith("@flat")
            ):
                return True
            if _has_special_keys(val):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _has_special_keys(item):
                return True
    return False


# Re-export commonly used functions
def escape_xml(s: str) -> str:
    """Escape special XML characters in a string."""
    if _USE_RUST and rust_escape_xml is not None:  # pragma: no cover
        return rust_escape_xml(s)
    else:
        return _py_dicttoxml.escape_xml(s)


def wrap_cdata(s: str) -> str:
    """Wrap a string in a CDATA section."""
    if _USE_RUST and rust_wrap_cdata is not None:  # pragma: no cover
        return rust_wrap_cdata(s)
    else:
        return _py_dicttoxml.wrap_cdata(s)


# Export the same API as the original dicttoxml module
__all__ = [
    "dicttoxml",
    "escape_xml",
    "wrap_cdata",
    "is_rust_available",
    "get_backend",
]
