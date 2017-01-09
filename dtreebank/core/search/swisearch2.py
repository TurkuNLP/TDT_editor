# -*- coding: utf-8 -*-

# This code uses PLY to parse the search expressions

import re
import sys
import urllib


import dtreebank.core.search.swicomm as swi
from dtreebank.core.search.searchexpression import prologRealization

# def PLEsc(ustr):
#     return ustr.replace(u"'",ur"\'")




def initSearch(treesets,indices=None,gui=True):
    global allTreesets
    swi.startPL() #A no-op if swi has already been initialized and is only being reloaded
    swi.evalInPL("cleanup.") #A no-op if swi has just been initialized and is not being reloaded
    #swi.evalInPL("cleanupdata.") #A no-op if swi has just been initialized and is not being reloaded
    swi.loadTreesets(treesets,indices,gui)
    allTreesets=treesets

def stopSearch():
    pass
    
def doSearch(expr,caseSensitive=False,tsetidx=None):
    global allTreesets
    """tsetidx can restrict the search to a particular treeset index, if None, all treesets are considered"""
    #returns a list of [treesetidx, sentidx, [list of matching tokens if any]]
    if expr in [u"WASNULL",u"TOKEN-CHANGE",u"TOKEN-CHANGE-X",u"TOKEN-CHANGE-H"]: #...add other searchable keywords to this list
        hits=[]
        for tsetIdx,tSet in enumerate(allTreesets):
            for tIdx,t in enumerate(tSet.sentences):
                tokens=[tokIdx for tokIdx,tok in enumerate(t.tokens) if expr in tok.misc.split(u"|")]
                if tokens:
                    hits.append([tsetIdx,tIdx,tokens])

        return hits, "direct"
    if expr==u"RNDARGS":
        #Want to find trees with RNDARG*, sort by it
        hits=[]
        for tsetIdx,tSet in enumerate(allTreesets):
            for tIdx,t in enumerate(tSet.sentences):
                for f in t.flags:
                    if f.startswith(u"RNDARG"):
                        hits.append([f,tsetIdx,tIdx,[]])
                        break
        hits.sort()
        for h in hits:
            del h[0] #remove the flag
        return hits, "direct"
    elif expr==u"REDWHITE":
        #Want to find sentences with multiple roots
        hits=[]
        for tsetIdx,tSet in enumerate(allTreesets):
            for tIdx,t in enumerate(tSet.sentences):
                isTree,isComplete,roots=t.sanityProperties()
                if not (isTree and isComplete):
                    hits.append([tsetIdx,tIdx,[]])
        hits.sort()
        return hits, "direct"
    elif expr==u"MULTIROOT":
        #Want to find sentences with multiple roots
        hits=[]
        for tsetIdx,tSet in enumerate(allTreesets):
            for tIdx,t in enumerate(tSet.sentences):
                isTree,isComplete,roots=t.sanityProperties()
                if len(roots)>1:
                    hits.append([tsetIdx,tIdx,roots])
        hits.sort()
        return hits, "direct2"
    else:
        headT,exprPL=prologRealization(expr,caseSensitive)
        print >> sys.stderr, repr(exprPL)
        if tsetidx!=None:
            exprPL=u"TSetIdx=%d, "%tsetidx+exprPL
        rawresult=swi.doSearch(exprPL,headT)
        resDict={} #key: (tsetidx, sentidx) val: list of tokens
        for tsetidx, treeidx, match in rawresult:
            resDict.setdefault((tsetidx,treeidx),[]).append(match)
        #now sort the whole deal
        result=[(tsetidx,treeidx,matches) for ((tsetidx,treeidx),matches) in resDict.items()]
        for temp1,temp2,matches in result:
            matches.sort()
        result.sort()
        return result, headT+u": "+exprPL

def searchUrl(expr,hostpath=u"http://localhost:12346/"):
    #Returns search url as an expression
    pVar,pRel=prologRealization(expr,False)
    return hostpath+u"?query="+urllib.quote_plus(u"assert( ( tokenQuery(TSetID,SentID,%s) :- ( %s ) ) )."%(pVar,pRel))
    
if __name__=="__main__":
    import urllib
    expr=u"@CGBASE/A|D/@TXTRE/X/ </cop/ _  >/nsubj/ (_ !>/cop/ _)"
    expr=u"@CGTAG/V+T/ </cop/ _"
    expr=u"_ </nommod/ _"
    pVar,pRel=prologRealization(expr,False)
    print searchUrl("_ </nommod/ _")
