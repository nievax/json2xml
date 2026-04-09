'''
transform Controlled Vocabularies from iqb.JSON format (source) to DSpace.XML format (target):

Read CVs from source_URIs (see cv_list.json),
compare with existing source files in source path,
if different / new version:
    transform from JSON to XML format,
    and write to target path (see below)
'''

import json
import datetime
import requests

TARGET_FOLDER               = "../"
SOURCE_FOLDER               = TARGET_FOLDER + "transform/"
CV_LIST_FILE                = SOURCE_FOLDER + "cv_list.json"
LOGFILE_transform           = SOURCE_FOLDER + "transform.log"
LOGFILE_cronjob             = SOURCE_FOLDER +      "cron.log"
TIMEOUT                     = 60                                # seconds
PROLOG                      = '<?xml version=\"1.0\" encoding=\"utf-8\"?>'
any_changes: bool           = False
# TODO move these to config file:
# NODE_STR_JSON               = ""
NODE_STR_XML                = "node"
COMMMENT_STR_JSON           = "definition"
COMMMENT_STR_XML            = "hasNote"
SUBTREE_STR_JSON            = "narrower"
SUBTREE_STR_XML             = "isComposedBy"
LABEL_STR_JSON              = "prefLabel"
LABEL_STR_XML               = "label"

def read_file(     path: str)                                   -> str:
    ''''read content from file in path'''
    with open(path,      encoding="utf-8") as file:             # includes file closing
        file_as_string      = file.read()
    return file_as_string

def write_file(    path: str, content:str)                      -> None:
    ''''write content to file in path'''
    with open(path, "w", encoding="utf-8") as file:             # includes file closing
        file.write(content)

def add_to_file(   path: str, content:str)                      -> None:
    '''append content to file in path'''
    with open(path, "a", encoding="utf-8") as file:             # includes file closing
        file.write(content)

def check_for_request_errors(response,     request_url)         -> None:
    '''check http request for errors'''
    try:
        response.raise_for_status()
    except    requests.exceptions.HTTPError                       as request_error:
        raise RuntimeError(request_url  + ' / request_error: ' + str(request_error.response.status_code)
                                        + ' / '                +     request_error.response.reason)      \
                                                                from request_error

def read_json_uri(      request_url: str,
                        json_content = None,
                        headers      = None,
                        timeout      = TIMEOUT, ):  # response.json() may be: a dict (if != fis) or a list (if == fis)
    '''read a request response that is given as JSON'''
    # using with ensures that the file is properly closed when reading has finished:
    with requests.get(  request_url,
                        json    = json_content,
                        headers = headers,
                        timeout = timeout,)      as response:   # response: Http
        response.headers['Access-Control-Allow-Origin'] = '*'   # for base.html/CORS
        check_for_request_errors(response, request_url)
    return  response.json()

def transform_to_xml(topterms: list, test_cv:dict)              -> str:
    '''transform the source object to an XML string'''
    term_nodes: str         = ''
    line_break: str         = '\r\n'
    line0:      str         = PROLOG + line_break
    root_attributes: dict   = { 'id':                              "0",
                                 LABEL_STR_XML:                     test_cv["targetfile"],
                                'xmlns:xsi':                       "http://www.w3.org/2001/XMLSchema-instance",
                                'xsi:noNamespaceSchemaLocation':   "controlledvocabulary.xsd",
                                }

    def open_tag( tagname: str, attributes: dict|None = None, cont:    str = '') -> str:
        '''open tag string'''
        attribute_strings           = ""
        if  attributes is not None:
            for key, value in attributes.items():
                attribute_strings  +=  ' ' + key + '="' + value + '"'
        opening_symbol              =  '<'
        if  cont != '':
            closing_symbol          =  '>'
        else:   # cont == '' / empty is True:
            closing_symbol          = '/>'
        return '       '    + opening_symbol + tagname + attribute_strings  + closing_symbol

    def close_tag(tagname: str)                                                  -> str:
        '''close tag string'''
        return '       '    + '</'           + tagname                      + '>'

    def make_node(tagname: str, attributes: dict|None = None, content: str = '') -> str:
        '''generate a tag string'''
        if  content     != '':
            element     = open_tag(  tagname, attributes, content)  + line_break    \
                        + content                                   + line_break    \
                        + close_tag( tagname)                       + line_break
        else:   # content == ""
            element     = open_tag(  tagname, attributes)           + line_break    # empty_tag
        return element

    def escape_xml_chars(term: str)                             -> str:
        '''replace characters that are essential for XML'''
        esc_term                = ""
        esc_characters          = { '"':    "&quot;",
                                    "&":    "&amp;",
                                    "'":    "&apos;",
                                    "<":    "&lt;",
                                    ">":    "&gt;",
                                }
        for character in term:
            to_escape           = False
            for key, value     in esc_characters.items():
                if  character  == key:
                    to_escape   = True
                    esc_term   += value
                    break
            if  to_escape      is False:
                    esc_term   += character
        return      esc_term

    def build_term_xml(  term, cv_id:str, j:int)                -> str:
        '''CV-specific: build an XML block for a single term with its subterms (recursively)'''
        id_number:  str
        label:      str             = ""
        cont:       str             = ""
        if  cv_id                  != "fis":       # term is dict
            id_number               = term["id"].rsplit("/", 1)[1]               # number behind last /
            if  LABEL_STR_JSON    in  term:
                if  "de"          in  term[LABEL_STR_JSON]:
                    label          =  term[LABEL_STR_JSON]["de"]
            if  COMMMENT_STR_JSON in  term:
                if  "de"          in  term[COMMMENT_STR_JSON]:
                    cont           += make_node(COMMMENT_STR_XML, None, term[COMMMENT_STR_JSON]["de"])
            if  SUBTREE_STR_JSON  in  term:                 # cannot become a fct. because of recursivity
                subterms:list[dict] = term[SUBTREE_STR_JSON]
                subterm_nodes       = ""
                for subterm       in  subterms:
                    subterm_nodes  += build_term_xml(subterm, cv_id, j)
                cont               += make_node(SUBTREE_STR_XML,  None, subterm_nodes)
        else:                   # cv_id == "fis" => term is str
            id_number               = str(j)
            label                   = escape_xml_chars(term)
        return make_node(NODE_STR_XML, {'id': id_number, LABEL_STR_XML: label}, cont)

    for i, topterm in enumerate(topterms, start=1):
        term_nodes                 += build_term_xml(topterm, test_cv["id"], i)
    xml_text                        =  line0 +  make_node(NODE_STR_XML,
                                                            root_attributes,
                                                            make_node(SUBTREE_STR_XML, None, term_nodes),
                                                            )
    return xml_text
# return_value = parseString(xml_data).toprettyxml(encoding="UTF-8").decode()

def write_files(filetype: str, path: str, new_cv: str)          -> None:
    '''save new and also old versions of json source and xml target for quality control'''
    full_path_new    = path +     "."  + filetype
    full_path_old    = path + "_old."  + filetype
    old_cv: str      = read_file(full_path_new)
    write_file(full_path_old,   old_cv)
    write_file(full_path_new,   new_cv)

timestring                  = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
file_content:       dict    = json.loads(read_file(CV_LIST_FILE))
add_to_file(LOGFILE_cronjob, timestring                                            + "\r\n")
for cv in file_content["controlled_vocabularies"]:
    if      cv["targetfile"]:           # if cv is used in DSpace
        if  cv["id"]                != "fis":
            new_test_cv_uri         = file_content["source_uri_part"]   + cv["id"] + "/index.json"
        else:                           # cv["id"] == "fis" (i.e. keywords)
            new_test_cv_uri         = file_content["source_uri_fis"]
        # cv_contents may be: a dict (if != fis) or a list (if == fis)
        new_cv_content              = read_json_uri(new_test_cv_uri)
                                # a proxy prevents the API from being called with default python User-Agent:
                                                    # headers = {'User-Agent': 'xyz', },
                                                    # timeout = 5,
        source_path                 = SOURCE_FOLDER                     + cv["sourcefile"]
        target_path                 = TARGET_FOLDER                     + cv["targetfile"]
        old_cv_content              = json.loads(read_file(source_path  + ".json"))
        # compare dicts instead of files, so file formatting / beautifying makes no difference:
        if  new_cv_content         != old_cv_content:
            if  cv["id"]           != "fis":
                cv_topterms         = new_cv_content["hasTopConcept"]       # list[dict]
            else:                       # cv["id"] == "fis"
                cv_topterms         = new_cv_content                        # list[string]
            write_files("json", source_path, json.dumps(  new_cv_content, indent=4))
            write_files("xml",  target_path, transform_to_xml(cv_topterms, cv))
            logtext                 = timestring + " - "  \
                                    + cv["sourcefile"] + ".json (" + cv["targetfile"] + ".xml)"            + "\r\n"
            add_to_file(LOGFILE_transform, logtext)
            changed_bool            = "   "
            marker                  = "            #"
            any_changes             = True
        else:   # new_cv_content   == old_cv_content
            changed_bool            = "NOT"
            marker                  = ""
        add_to_file(LOGFILE_cronjob, "Files were "     + changed_bool  + " changed: " \
                                    + cv["sourcefile"] + ".json (" + cv["targetfile"] + ".xml) " + marker  + "\r\n")
add_to_file(        LOGFILE_cronjob, "---------------------------------------------------------"           + "\r\n")
print("transform.py has run ...")
if  any_changes is True:
    print("... and some Controlled Vocabularies were updated.")
else:
    print("... and no Controlled Vocabulary needed to be updated.")
