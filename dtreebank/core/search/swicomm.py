import subprocess as subp
import codecs

import re
import platform
import sys
import os.path

DIR=os.path.dirname(os.path.abspath(__file__))
#Loading the swiiface module

try:
    pyMaj,pyMin,pyPatch=platform.python_version_tuple()
    if pyMaj!="2":
        print >> sys.stderr, "You need a 2.x Python for this program to work"
        sys.exit(1)
    if pyMin=="6":
        import dtreebank.core.search.pybin26.swiiface as swi
    elif pyMin=="5" and platform.system()=="Linux":
        import dtreebank.core.search.pybin25.swiiface as swi
    elif pyMin=="7" and platform.system()=="Linux":
        import dtreebank.core.search.pybin27.swiiface as swi
    else:
        import dtreebank.core.search.swiiface as swi
except:
    print >> sys.stderr, "Exception info:",sys.exc_info()
    print >> sys.stderr, "API version:",sys.api_version
    print >> sys.stderr, "Python version:",sys.version_info
    print >> sys.stderr
    if pyMin in ("56"): #Supported version, not working...
        print >> sys.stderr, "Importing the SWI interface module did not succeed, even though your version of Python should be supported. Try to see if you can re-compile using the information in the README file and let me (ginter@cs.utu.fi) know how it went and whether you need help. Sorry for the trouble."
    else:
        print >> sys.stderr, "There is no pre-compiled version of the swiiface module for python versions other than 2.5 and 2.6. You need to compile swiiface yourself (see the README files) and place the resulting .so file (on linux) or .pyd file (on Windows) to the main directory of the Annotator program. Then try to re-start."
    sys.exit()

resultPairRe=re.compile(ur"\[([0-9]+), ([0-9]+), ([0-9]+)\]",re.U) #one result field: [TSetID,SentID,tokenSeq]
swiProcess=None

tempFileCounter=0 #used to produce unique temp filenames

PLRunning=False #State flag to see if PL is up and initialized

"""Interface to Prolog

* call startPL() before you do anything else
* call stopPL() when with everything
* doSearch() is the main function to be used
  - it cleans up first (removes all tokenQuery/2 predicates)
  - asserts the corresponding tokenQuery/2 predicate
  - calls doSearch/1
"""

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


def evalInPL(command):
    swi.callPL(uString2pl(command))
    
def startPL():
    """Starts SWI prolog and returns the running process."""
    global PLRunning
    if PLRunning:
        return
    #Find the appropriate library to point Prolog to
    print >> sys.stderr, swi.__file__
    swi.initPL(swi.__file__)
    swi.callPL("set_prolog_flag(debug_on_error,false)")
    swi.callPL("working_directory(_,'%s')"%DIR)
    swi.callPL("consult(search_common)")
    PLRunning=True

def stopPL():
    """Quits SWI prolog"""
    pass #TODO

#This is token search
def doSearch(searchClause,headTokenVariable):
    """searchClause is the RH-side of the search clause
    headTokenVariable is the variable that represents the main result token -> a list of these is returned"""

    resultList=[]

    evalInPL("cleanup.")
    assertClause=u"assert( ( tokenQuery(TSetID,SentID,%s) :- ( %s ) ) )."%(headTokenVariable,searchClause)
    evalInPL(assertClause)
    resultList=swi.matchingSentences()
    return resultList


def unloadTreesets(indices,gui=True):
    """indices is a list of dirty treeset indices that need a wipe"""
    for idx in indices:
        evalInPL("unloadtreeset(%d)."%idx)
    

def loadTreesets(treesets,indices=None,gui=True):
    """Loads all treesets in the list to Prolog. indices gives a list of treesets to load, if None, all will be loaded"""
    global tempFileCounter
    if indices==None:
        indices=range(len(treesets))
    else:
        unloadTreesets(indices,gui) #unload first if we have some indices
    if not indices:
        return
    lines=[]
    prologOut=os.path.join(DIR,"temp%d.pl"%tempFileCounter) #need to make these files unique so that SWI does not reconsult them (removing predicates already loaded previously)
    tempFileCounter+=1
    f=open(prologOut,"wt")

    if gui:
        import PyQt4.QtCore
        import PyQt4.QtGui
        progress=PyQt4.QtGui.QProgressDialog("Exporting %d treesets to Prolog..."%len(indices), "Stop", 0, len(indices), None);
        progress.setWindowModality(PyQt4.QtCore.Qt.WindowModal);
        progress.setRange(1,len(indices))
    counter=0

    for treesetId in indices:
        treeset=treesets[treesetId]
        for treeId,tree in enumerate(treeset.sentences):
            lines.extend(tree.prologRep(treesetId,treeId))
        counter+=1
        if gui:
            progress.setValue(counter)
            if progress.wasCanceled():
                break
    lines.sort()
#    print >>f, ":-dynamic tokenQuery/3,dep/5,token/4,cgreading/5,twolreading/5,arg/5,flag/5,frame/4."
    for line in lines:
        print >> f, uString2pl(line)
    f.close()
    evalInPL("consult('%s')."%prologOut)
    os.remove(prologOut)





