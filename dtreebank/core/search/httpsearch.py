# -*- coding: utf-8 -*-
import os.path
import sys
import urllib
import httplib

from dtreebank.core.search.searchexpression import assertStatement


def uString2pl(s,encoding="utf-8"):
    """Turns s into a suitable atom representation for prolog. s is either
a unicode string or a standard string encoded using the given encoding
(default utf-8)."""

    if isinstance(s,str):
        s=unicode(s,encoding)
    elif not isinstance(s,unicode):
        raise ValueError, "Expected str or unicode"
    #s is guaranteed to be unicode at this point
    #now turn into the escaped version
    s=s.encode("unicode_escape")
    #Now s is a standard ASCII string with \x and \u escapes in it
    #these escapes are readily understood by prolog
    s=s.replace(r"\\'",r"\'").replace(r"\\+",r"\+").replace(r"\\=",r"\=") #ununescape (what a word...) the quotes and +
    return s


def getUrlSearchString(expr,caseSensitive):
    #Returns search url as an expression
    aStatement=assertStatement(expr)
    return u"?query="+urllib.quote_plus(uString2pl(aStatement))


def doSearch(expr,port=u"12345",host=u"localhost",caseSensitive=False):
    
    urlSearchString=getUrlSearchString(expr,caseSensitive)
    conn=httplib.HTTPConnection(host+u":"+port)
    conn.request("GET", u"/"+urlSearchString)
    resp=conn.getresponse()
    responseLines=unicode(resp.read(),"utf-8").split(u"\n")
    conn.close()

    resDict={} #key: (tsetidx, sentidx) val: list of tokens
    for line in responseLines:
        line=line.strip()
        if line.startswith(u"tokenhit: "):
            label,treesetIdx,treeIdx,tokenIdx=line.split()
            treesetIdx,treeIdx,tokenIdx=int(treesetIdx),int(treeIdx),int(tokenIdx)
            resDict.setdefault((treesetIdx,treeIdx),[]).append(tokenIdx)
    for lst in resDict.itervalues():
        lst.sort()
    result=[(tsetIdx,treeIdx,tokenIndices) for ((tsetIdx,treeIdx),tokenIndices) in resDict.iteritems()]
    result.sort()
    return result

if __name__=="__main__":
    if len(sys.argv)>1:
        print doSearch(u"/on/",sys.argv[1])
    else:
        print doSearch(u"/on/")
