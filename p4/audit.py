"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint


OSMFILE = "oc.osm"
street_type = re.compile(r'\b\S+\.?$', re.IGNORECASE)
zip_type = re.compile(r'^\d{5}(?:[-\s]?\d{4})?$')


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Circle", "Crescent", "Gate", "Terrace", "Grove", "Way"]

nesw_mapping = { 
            "N.": "North",
            "N": "North",
            "E.": "East",
            "E": "East",
            "S.": "South",
            "S": "South",
            "W.": "West",
            "W": "West"
            }

street_mapping = {
                    "Ave.": "Avenue",
                    "Aven": "Avenue",
                    "Ave": "Avenue",
                    "Blvd.": "Boulevard",
                    "Blvd": "Boulevard",
                    "Cir.": "Circle",
                    "Cir": "Circle",
                    "Ct.": "Court",
                    "Ct": "Court",
                    "Crt.": "Court",
                    "Crt": "Court",
                    "Dr.": "Drive",
                    "Dr": "Drive",
                    "St.": "Street",
                    "St": "Street",
                    "Rd.": "Road",
                    "Rd": "Road",
                    "Trl.": "Trail",
                    "Trl": "Trail"
                }

viet_mapping = {
        '\u00C0' : 'A',
        '\u00C1' : 'A',
        '\u00C2' : 'A',
        '\u00C3' : 'A',
        '\u00C8' : 'E',
        '\u00C9' : 'E',
        '\u00CA' : 'E',
        '\u00CC' : 'I',
        '\u00CD' : 'I',
        '\u00D2' : 'O',
        '\u00D3' : 'O',
        '\u00D4' : 'O',
        '\u00D5' : 'O',
        '\u00D9' : 'U',
        '\u00DA' : 'U',
        '\u00DD' : 'Y',
        '\u00E0' : 'a',
        '\u00E1' : 'a',
        '\u00E2' : 'a',
        '\u00E3' : 'a',
        '\u00E8' : 'e',
        '\u00E9' : 'e',
        '\u00EA' : 'e',
        '\u00EC' : 'i',
        '\u00ED' : 'i',
        '\u00F2' : 'o',
        '\u00F3' : 'o',
        '\u00F4' : 'o',
        '\u00F5' : 'o',
        '\u00F9' : 'u',
        '\u00FA' : 'u',
        '\u00FD' : 'y',
        '\u0102' : 'A',
        '\u0103' : 'a',
        '\u0110' : 'D',
        '\u0111' : 'd',
        '\u0128' : 'I',
        '\u0129' : 'i',
        '\u0168' : 'U',
        '\u0169' : 'u',
        '\u01A0' : 'O',
        '\u01A1' : 'o',
        '\u01AF' : 'U',
        '\u01B0' : 'u',
        '\u1EA0' : 'A',
        '\u1EA1' : 'a',
        '\u1EA2' : 'A',
        '\u1EA3' : 'a',
        '\u1EA4' : 'A',
        '\u1EA5' : 'a',
        '\u1EA6' : 'A',
        '\u1EA7' : 'a',
        '\u1EA8' : 'A',
        '\u1EA9' : 'a',
        '\u1EAA' : 'A',
        '\u1EAB' : 'a',
        '\u1EAC' : 'A',
        '\u1EAD' : 'a',
        '\u1EAE' : 'A',
        '\u1EAF' : 'a',
        '\u1EB0' : 'A',
        '\u1EB1' : 'a',
        '\u1EB2' : 'A',
        '\u1EB3' : 'a',
        '\u1EB4' : 'A',
        '\u1EB5' : 'a',
        '\u1EB6' : 'A',
        '\u1EB7' : 'a',
        '\u1EB8' : 'E',
        '\u1EB9' : 'e',
        '\u1EBA' : 'E',
        '\u1EBB' : 'e',
        '\u1EBC' : 'E',
        '\u1EBD' : 'e',
        '\u1EBE' : 'E',
        '\u1EBF' : 'e',
        '\u1EC0' : 'E',
        '\u1EC1' : 'e',
        '\u1EC2' : 'E',
        '\u1EC3' : 'e',
        '\u1EC4' : 'E',
        '\u1EC5' : 'e',
        '\u1EC6' : 'E',
        '\u1EC7' : 'e',
        '\u1EC8' : 'I',
        '\u1EC9' : 'i',
        '\u1ECA' : 'I',
        '\u1ECB' : 'i',
        '\u1ECC' : 'O',
        '\u1ECD' : 'o',
        '\u1ECE' : 'O',
        '\u1ECF' : 'o',
        '\u1ED0' : 'O',
        '\u1ED1' : 'o',
        '\u1ED2' : 'O',
        '\u1ED3' : 'o',
        '\u1ED4' : 'O',
        '\u1ED5' : 'o',
        '\u1ED6' : 'O',
        '\u1ED7' : 'o',
        '\u1ED8' : 'O',
        '\u1ED9' : 'o',
        '\u1EDA' : 'O',
        '\u1EDB' : 'o',
        '\u1EDC' : 'O',
        '\u1EDD' : 'o',
        '\u1EDE' : 'O',
        '\u1EDF' : 'o',
        '\u1EE0' : 'O',
        '\u1EE1' : 'o',
        '\u1EE2' : 'O',
        '\u1EE3' : 'o',
        '\u1EE4' : 'U',
        '\u1EE5' : 'u',
        '\u1EE6' : 'U',
        '\u1EE7' : 'u',
        '\u1EE8' : 'U',
        '\u1EE9' : 'u',
        '\u1EEA' : 'U',
        '\u1EEB' : 'u',
        '\u1EEC' : 'U',
        '\u1EED' : 'u',
        '\u1EEE' : 'U',
        '\u1EEF' : 'u',
        '\u1EF0' : 'U',
        '\u1EF1' : 'u',
        '\u1EF2' : 'Y',
        '\u1EF3' : 'y',
        '\u1EF4' : 'Y',
        '\u1EF5' : 'y',
        '\u1EF6' : 'Y',
        '\u1EF7' : 'y',
        '\u1EF8' : 'Y',
        '\u1EF9' : 'y'
        }
                   

def audit_street_type(street_types, street_name):
    m = street_types.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_phone(elem):
    return (elem.attrib['k'] == "phone")

def is_zip(elem):
    return (elem.attrib['k'] == "addr:postcode")


def substitute(name, mapping):
    """Replaces characters in a string as defined by the given dictionary mapping"""
    
    subbed_name = name
    for key in mapping.keys():
        if key in name:
            subbed_name = re.sub(key, mapping[key], subbed_name)
    return subbed_name

def update_zip(zip):
    """standardizes zip code to xxxxx or xxxxx-xxxx"""
    
    if zip.lower() == 'disneyland':
        return '92802'
    noletters = re.sub(r'^\D*|[a-zA-Z]|^D*$', '', zip)
    if zip_type.match(noletters):
        numbers = re.sub(r'\D', '', noletters)
        if len(numbers) == 5:
            return numbers
        elif len(numbers) == 9:
            numbers = numbers[:5] + '-' + numbers[5:]
            return numbers
    else:
        return None


def update_phone(number):
    """standardize phone number to 10 consecutive digits"""
    
    digits = re.sub(r'[^0-9]', '', number)
    if re.match(r'^1\d{10}$', digits):
        digits = digits[1:]
    if re.match(r'\d{10}$', digits):
        return digits
    else:
        return None


def update_name(name):
    """cleans street name"""

    # standardize Vietnamese names
    better_name = substitute(name, viet_mapping)
   
    # spell out abbreviated directions if they're found in the beginning or middle of the name
    for key in nesw_mapping.keys():
        better_name = re.sub (r'\s' + re.escape(key) + r'\s', ' ' + nesw_mapping[key] + ' ', better_name, flags=re.I)
        better_name = re.sub (r'^' + re.escape(key) + r'\s', nesw_mapping[key] + ' ', better_name, flags=re.I)
    
    # spell out abbreviated names at the end of name
    for key in street_mapping.keys():
        better_name = re.sub(r'\s' + re.escape(key) + r'$', ' ' + street_mapping[key], better_name, flags=re.I)

    return better_name
    

