#!/usr/bin/env python
from lxml import etree
import sys
from collections import defaultdict
from timeit import timeit
import re

TAG_PREFIX = "{http://www.mediawiki.org/xml/export-0.4/}"
TERM_TABLE_NAME = "temp_dict"
DEF_TABLE_NAME = "temp_def"

def extract_dictionary():
    filename = "enwiktionary-20100824-pages-articles.xml"
    context = etree.iterparse(filename)
    count = 0
    current_thing = defaultdict(str)
    results = []
    defre = re.compile("# .*")
    for event, elem in context:

        #if count > 500: raise StopIteration()

        if event == 'end':
            current_thing[elem.tag.replace(TAG_PREFIX, '')] = elem.text
                
            if elem.tag == TAG_PREFIX+"page":
                if current_thing['text']:
                    if "# " in current_thing['text'] and "{{en-" in current_thing['text']:
                        count += 1
                        yield {
                            'term' : current_thing['title'].encode('utf-8'),
                            'count' : count,
                            'definitions' : defre.findall(current_thing['text'].encode('utf-8'))
                            }
                    del current_thing
                    current_thing = defaultdict(str)
                while elem.getparent() is not None:
                    del elem.getparent()[0]

def sqlify(record):
    global TERM_TABLE_NAME, DEF_TABLE_NAME
    outstr = "INSERT INTO %s (id, term) VALUES (%d, '%s');\n" % (
        TERM_TABLE_NAME,
        record['count'],
        record['term'].replace("'", "\\'"),
        )
    for definition in record['definitions']:
        outstr += "INSERT INTO %s (id, term_id, definition) VALUES (NULL, %s, '%s');\n" % (
            DEF_TABLE_NAME,
            record['count'],
            definition.replace("'", "\\'"),
            )
    return outstr

def create_sql_tables():
    global TERM_TABLE_NAME, DEF_TABLE_NAME
    outstr = "DROP TABLE IF EXISTS %s; CREATE TABLE %s (id int, term varchar(255));\n" % (
        TERM_TABLE_NAME, TERM_TABLE_NAME
        )
    outstr += "DROP TABLE IF EXISTS %s; CREATE TABLE %s (id int not null auto_increment, term_id int, definition text, primary key (id));\n" % (
        DEF_TABLE_NAME, DEF_TABLE_NAME
        )
    return outstr

if __name__ == "__main__":
    filename = "enwiktionary-20100824-pages-articles.xml"
    try:
        filename = sys.argv[1]
    except Exception, e:
        pass
    outfile = open('out.sql','w')

    outfile.write(create_sql_tables())
    print "begin"
    for d in extract_dictionary():
        outfile.write(sqlify(d))
    outfile.close()
    print "done"
