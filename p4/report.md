
# OpenStreetMap Data Case Study 
Jeremy Tran  
January 31, 2018 

## Map Area
Orange County, CA, USA
- https://www.openstreetmap.org/relation/396466

Orange County is my hometown, a common pick for this project it seems. 

I used Mapzen to download information for the square area bounded by "-118.1259,33.333992,-117.412987,33.947514" on December 2, 2017.  Mapzen shut down shortly after I took the sample so I do not know if the portion I took has been significantly updated since then but for the purposes of this study I think the downloaded information should be sufficient.

## Problems Encountered in the Map/Data
I imported the data into SQLite through a provisionary process.py and tried to take a sample using sample.py with which I can test auditing code.

### Python 2 vs 3 and Unicode
I opted to use Python 3 as opposed to Python 2 as provided by most of the class examples, partly because I've used Python 2 in the past and felt like it would be a minor exercise to update code to Python 3 (without using the 2to3 tool).  The most frequent changes were adding parentheses to the `print` function, and replacing `dict.iteritems()` with `iter(dict.items())`.

Initially I encountered a few `'charmap' codec can't decode byte 0x9d in position 713: character maps to <undefined>` error messages when trying to sample my downloaded osm file, which were resolved by adding the `encoding='utf-8'` argument to the `with open()` function.

Similarly, the extended `UnicodeDictWriter` function kept outputting `'b'` to the csv files with Python 3's more stringent handling of bytes vs Unicode.  I figured the `DictWriter` function does not need to be extended in Python 3 anyway, and again adding the `encoding='utf-8'` argument ensured Unicode output.

### Vietnamese characters
After examining several of the initial Unicode error messages I encountered, I found the source to be the usage of Vietnamese characters that combined Latin characters with multiple accent marks and such.  I decided to standardize such names by replacing their Unicode with the ASCII equivalent as detailed by this character set http://vietunicode.sourceforge.net/charset/.  Although Python 3 is sufficiently able to handle Unicode character sets, other applications (such as the Windows console) may be less adept at handling various non-standard symbols and output Mojibake instead.

```python
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
        ...
        }

def substitute(name, mapping):
    """Replaces characters in a string as defined by the given dictionary mapping"""
    
    subbed_name = name
    for key in mapping.keys():
        if key in name:
            subbed_name = re.sub(key, mapping[key], subbed_name)
    return subbed_name
```

### Overly Abbreviated Street Names
I took random (< 0.0001) samples of street names

```sql
sqlite> SELECT tag.value FROM
   ...> (SELECT * FROM NODES_TAGS
   ...> UNION ALL
   ...> SELECT * FROM WAYS_TAGS) tag
   ...> WHERE tag.key = 'street' AND random() <= 0.0001;
```

which yielded variously overly abbreviated names as 

```
Knowlwood Ct
Tuscany Rd
N Euclid St
```

So I added more values to the dictionary and updated the `update_name` function.

```python
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
                    ...
                  }

def update_name(name):
    """cleans street name"""

    # standardize Vietnamese names
    better_name = substitute(name, viet_mapping)
   
    # spell out abbreviated directions if they're found in the beginning or middle of the name
    for key in nesw_mapping.keys():
        better_name = re.sub (r'\s' + re.escape(key) + r'\s', ' ' + nesw_mapping[key] + ' ', better_name, flags=re.I)
        better_name = re.sub (r'^' + re.escape(key) + r'\s', nesw_mapping[key] + ' ', better_name, flags=re.I)
    
    # spell out abbreviated streets at the end of names
    for key in street_mapping.keys():
        better_name = re.sub(r'\s' + re.escape(key) + r'$', ' ' + street_mapping[key], better_name, flags=re.I)

    return better_name
```

### Non-standard Zip Codes
Running a query of postal zip codes

```sql
sqlite> SELECT tag.value, COUNT(*) as count 
   ...> FROM (SELECT * FROM nodes_tags 
   ...> UNION ALL 
   ...> SELECT * FROM ways_tags) tag
   ...> WHERE tag.key='postcode'
   ...> GROUP BY tags.value
   ...> ORDER BY count DESC;
```

yielded quite a few non-standard formats, last one particularly standing out.
```
92843|1
92868-3100|1
92879|1
92880-6970|1
93688|1
CA 92614|1
CA 92630|1
CA 92646|1
CA 92651|1
Disneyland|1
```

I added a regular expression and function to format zip codes thusly:

```python
zip_type = re.compile(r'^\d{5}(?:[-\s]?\d{4})?$')

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
```

### Numerous (Correct) Phone Formats
Randomly sampling phone numbers

```sql
sqlite> SELECT tag.value FROM
   ...> (SELECT * FROM NODES_TAGS
   ...> UNION ALL
   ...> SELECT * FROM WAYS_TAGS) tag
   ...> WHERE tag.key = 'phone' AND random() <= 0.0001;
```

yielded phone numbers written in various formats, albeit all correctly (except for the last one).

```
(949) 859-1455
951-273-5000
+1-800-777-0133
+1-949-582-9666
800 213-4184 or 951 273-0281
```

For the purposes of standardizing and consolidating the data I decided 10 digit to be the best representation, with the reader then formatting the phone number output as necessary.

```python
def update_phone(number):
    """standardize phone number to 10 consecutive digits"""
    
    digits = re.sub(r'[^0-9]', '', number)
    if re.match(r'^1\d{10}$', digits):
        digits = digits[1:]
    if re.match(r'\d{10}$', digits):
        return digits
    else:
        return None
```

## Data Overview
Following are basic statistics and SQL queries performed after the dataset had been cleaned and inputted into Sqlite.
 
### file sizes
```
oc.osm ........  962,722 kB
oc.db .......... 171,522 kB
nodes.csv ....... 86,981 kB
ways.csv ........ 30,607 kB
nodes_tags.csv .. 13,513 kB
ways_tags.csv ... 36,298 kB
ways_nodes.csv .. 24,106 kB
```
 
### number of nodes
```sql
sqlite> SELECT COUNT(*) FROM nodes;
1048575

```
 
### number of ways
```sql
sqlite> SELECT COUNT(*) FROM ways;
480178
```
 
### unique number of users
```sql
sqlite> SELECT COUNT (DISTINCT(U.UID)) FROM
   ...> (SELECT UID FROM ways
   ...> UNION ALL
   ...> SELECT UID FROM nodes) u;
1493
```
 
### top 10 contributors
```sql
sqlite> SELECT e.user, COUNT(*) as num
   ...> FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
   ...> GROUP BY e.user
   ...> ORDER BY num DESC
   ...> LIMIT 10;
SJFriedl|174347
Brian@Brea|163135
Aaron Lidman|150995
AM909|78389
frankthetankk|40941
dannykath_labuildings|39908
RichRico_labuildings|39732
calfarome_labuilding|39598
piligab_labuildings|39370
karitotp_labuildings|34261
```

Representing 5 of the top 10 users, 'labuildings' sounded like it could be a larger group venture or joint effort on the behalf of some organization, such as a commercial construction company or publication conducting research.  However, a cursory Google search of "la buildings" , with the top result being [Gin Wong: 5 LA projects by the modern architect - Curbed LA](https://la.curbed.com/2017/9/18/16328524/gin-wong-la-buildings-modern-googie-lax) revealed no clear responsible party.
 
### most popular cuisines
```sql
sqlite> SELECT nodes_tags.value, COUNT(*) as num
   ...> FROM nodes_tags 
   ...> JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
   ...> ON nodes_tags.id=i.id
   ...> WHERE nodes_tags.key='cuisine'
   ...> GROUP BY nodes_tags.value
   ...> ORDER BY num DESC;
american|66
mexican|62
pizza|53
italian|27
japanese|26
vietnamese|25
seafood|21
chinese|19
sushi|19
thai|18
```
An eclectic selection of dining locations reflects the diversity and varied tastes of the population of southern California.

## Ideas for Improvement
### Soliciting Contributions from Secondary Users
After reviewing the uses of OpenStreetMap and actual apps for which it has been used as the mapbase, including Niantic's Ingress and Pokemon Go, I thought it might be a viable idea to solicit contributions from users one level removed from the OpenStreetMap data.  Secondary users, as opposed to those directly involved in OpenStreetMap such as GPS trackers and developers, may be more readily able to locate landmarks or identify errors otherwise missed by those collecting data via automated means.

One way to implement this additional layer of interaction, which should probably be reserved for the most frequently used apps or those that refer to the OpenStreetMap data the most, is allow for user-submitted corrections and suggestions.  If certain submissions crop up enough times, or patterns arise over repeated submissions,a team (perhaps designated by locality) can then vet the changes to update OpenStreetMap.  In this way the data can remain most up-to-date for the regions that see the most use.

Naturally, contributions made in such a manner cannot be applied systematically across OpenStreetMap, and allowing easy edits opens up the gateway to messier data, but it may be a way for OpenStreetMap to adapt according to its actual usage.  
  
### Autopopulating Data from Other Sources
Considering how much information seems to be automatically input into OpenStreetMap, I looked at the most frequently used tag types (defined as the word preceding any colons by the class project guidelines)
```sql
sqlite> SELECT tag.type, COUNT(*) as num
   ...> FROM
   ...> (SELECT * FROM nodes_tags
   ...> UNION ALL
   ...> SELECT * FROM ways_tags) tag
   ...> GROUP BY tag.type
   ...> ORDER BY num DESC
   ...> LIMIT 10;
regular|645685
tiger|459135
addr|249980
turn|14504
source|12713
lanes|10324
gnis|7159
ref|6858
source_ref|5910
old_ref|3653

```
The 'tiger' type appeared at nearly 28% frequency that the 'regular' and 'addr' type appeared, combined.  Tiger is most likely related to the Garmin devices which automatically contribute data.
  
I thought it may help keep the map updated by having certain bots or scripts automatically screen for updates from certain APIs, such as Google's and BING, and public domain data such as from government sources.
  
Cons may be the licensing issues with sampling from proprietary data sources without express permission or licensing.  Gathering a large amount of data automatically may also result in much more data needing to be cleaned.


## Conclusions
The dataset for my selected region seems very messy and incomplete, but I suppose it is reflective of data being aggregated from many users on a large scale.  If there were a greater commercial or competitive purpose behind the project I suppose there could be greater quality of data at the loss of 'free' information not tainted by commercial interests.
