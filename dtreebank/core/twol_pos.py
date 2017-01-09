import os.path
import codecs
import sys
import warnings as w
import glob
import os.path
import cPickle as pickle
import unicodedata as udata
import re

sys.path.append("../..")
#Need to use the fully-qualified name because treeset imports twol_pos circularly
import dtreebank.core.treeset 


#Priority list to resolve POS conflicts when trying to guess the main POS category
posPriority=u"PRON,Q,C,V,ADV,A,N,PCP1,PCP2,ABBR,DV-MA,PROP,PP,FORGN".split(u",")

#Global variables for POS tag re-assignment
#Used to pick the more common dependency type in case there are several "governors"
dTypeCounts=None #{depType:count}
#Pick the most-likely POS for this dependency type
dTypePOSCounts=None #{deptype:{POS:count}
#Pick the most-likely full tag for this dependency type
dTypeAllTagCounts=None #{deptype:{full-tag:count}
#Lemma counts (for compounds, only the last member is chosen
lemmaCounts=None #{lemma:count}

def warn(msg):
    w.warn(msg.encode("utf-8"))

def ispunct(s):
    """s is a unicode string"""
    for c in s:
        #Unicode data category for the character: see http://www.fileformat.info/info/unicode/category/index.htm
        cat=udata.category(c) 
        #P stands for punctuation, Sm for mathematical symbols, Sk for modifier symbols
        if not (cat.startswith(u"P") or cat==u"Sm" or cat==u"Sk"): #none of the others? Not a punctuation
            return False
    return True #all characters in the string were punctuation, so the string is punctuation

numRe=re.compile(u"^[0-9.,:\u2012\u2013\u2014\u2015\u2053~-]+$",re.U) #The unicode chars are various dashes
def isnum(s):
    if numRe.match(s):
        return True
    else:
        return False


def gatherDepBasedStats(dxmlDir, outputFName):
    """Goes through all files in dxmlDir and gathers stats on most common UN-AMBIGUOUS POS for each deptype. Pickles the relevant data to outputFName"""

    global dTypeCounts,dTypePOSCounts,dTypeAllTagCounts,lemmaCounts
    dTypeCounts,dTypePOSCounts,dTypeAllTagCounts,lemmaCounts={},{},{},{}

    for f in glob.glob(os.path.join(dxmlDir,"*.d.xml")):
        tset=dtreebank.core.treeset.TreeSet.fromFile(f)
        for sNode in tset:
            dtypes=[[] for x in sNode.tokens]
            for g,d,dType in sNode.deps:
                dtypes[d].append(dType)
            for g,d,dType in sNode.deps:
                if dType==u"cop":
                    dtypes[g]=[x+"_cop" for x in dtypes[g]]
            for x in dtypes:
                if x==[]:
                    x.append(u"ROOT")
            for tokenTypes in dtypes:
                for dType in tokenTypes:
                    dTypeCounts[dType]=dTypeCounts.get(dType,0)+1
            
            for idx,token in enumerate(sNode.tokens):
                cgReadings=[x for x in token.posTags]####DANGER if x[0]]
                if len(cgReadings)==1:
                    pos,tags=pretty_format_taglist(cgReadings[0][2])
                    lemma=cgReadings[0][1].split(u"#")[-1] #pick only the last
                    lemmaCounts[lemma]=lemmaCounts.get(lemma,0)+1
                    pos=u"POS_"+pos
                    for dType in dtypes[idx]:
                        dct=dTypeAllTagCounts.setdefault(dType,{})
                        dct[pos+u"_"+tags]=dct.get(pos+u"_"+tags,0)+1
                        dct=dTypePOSCounts.setdefault(dType,{})
                        dct[pos]=dct.get(pos,0)+1
    f=open(outputFName,"w")
    pickle.dump((dTypeCounts,dTypeAllTagCounts,dTypePOSCounts,lemmaCounts),f,pickle.HIGHEST_PROTOCOL)
    f.close()

def resolve(wordform,readings,dType,autoReading):
    #IN: Readings are of the form [("POS_pos","CAT_tag|CAT_tag|CAT_tag|...","lemma"),...]
    #dType is the GS dependency type
    #autoReading - reading given to NON-TWOL tags (predicted by pos-tagger)
    #OUT: ("POS_pos","tags
    global dTypeCounts,dTypePOSCounts,dTypeAllTagCounts,lemmaCounts

    if ispunct(wordform):
        pos=u"POS_PUNCT"
        return (pos,u"",wordform), u"punct"
    elif wordform==u"*null*":
        pos=u"POS_NULLT"
        return (pos,u"",wordform), u"null"
    elif len(readings)==0:
        print >> sys.stderr, wordform.encode("utf-8")
        return (u"POS_UNK",u"",wordform), u"???"
    elif len(readings)==1:
        if readings[0][0]==u"POS_NON-TWOL":
            return autoReading, u"HunPos/NonTWOL"
        else:
            return readings[0], u"nonambiguous"
    #Disambiguate based on POS only first
    posCounts=[dTypePOSCounts.get(dType,{}).get(pos,0) for pos,tags,lemma in readings]
    maxCount=max(posCounts)
    readings=[reading for count,reading in zip(posCounts,readings) if maxCount==count]
    if len(readings)==1:
        return readings[0], u"postag"
    #So now we should have only same-pos readings open anymore, except in case where all counts were zero
    tagCounts=[dTypeAllTagCounts.get(dType,{}).get(pos+u"_"+tags,0) for pos,tags,lemma in readings]
    maxCount=max(tagCounts)
    readings=[reading for count,reading in zip(tagCounts,readings) if maxCount==count]
    if len(readings)==1:
        return readings[0], u"fulltag"
    #So now we should have only same-tag readings open anymore, except in case where all counts were zero
    #now try to prefer the non-concatenation lemma
    compoundCounts=[lemma.count(u"#") for pos,tags,lemma in readings]
    minCount=min(compoundCounts)
    readings=[reading for count,reading in zip(compoundCounts,readings) if count==minCount]
    if len(readings)==1:
        return readings[0], u"compoundcount"
    mainLemmaCounts=[lemmaCounts.get(lemma.split(u"#")[-1],0) for pos,tags,lemma in readings]
    maxCount=max(mainLemmaCounts)
    readings=[reading for count,reading in zip(mainLemmaCounts,readings) if count==maxCount]
    if len(readings)==1:
        return readings[0], u"mainlemmacount"
    #After this point, the decision is quite much arbitrary
    lemmaLengths=[len(lemma) for pos,tags,lemma in readings]
    maxCount=max(lemmaLengths)
    readings=[reading for count,reading in zip(lemmaLengths,readings) if count==maxCount]
    if len(readings)==1:
        return readings[0], u"wild"
    #Still can't decide? Oh boy...
    return readings[0], u"wild" #...just pick the first one

def guessedTagsForTreeset(tset):
    f=open("delme.hunpos","w")
    for tree in tset:
        for token in tree.tokens:
            print >> f, token.text.encode("utf-8")
        print >> f
    f.flush()
    f.close()
    os.system("/home/ginter/hunpos-1.0-linux/hunpos-tag /home/ginter/Convertus/strongmodel < delme.hunpos > delme_tagged.hunpos")
    sents=[[]]
    f=open("delme_tagged.hunpos","r")
    for line in f:
        line=line.strip().decode("utf-8")
        if not line:
            sents.append([])
        else:
            wordform,finetag=line.split(u"\t")
            components=finetag.split(u"_")
            assert len(components)%2==0 and len(components)>0
            pos=u"_".join(components[:2])
            tags=u"_".join(components[2:])
            sents[-1].append((pos,tags,wordform))
    f.close()
    sents=[s for s in sents if s!=[]]
    assert len(sents)==len(tset)
    return sents

def retagTreeset(tset):
    global dTypeCounts,dTypePOSCounts,dTypeAllTagCounts,lemmaCounts
    #I'll want to run this through HunPos to fill-in the NON-TWOLs
    autoTags=guessedTagsForTreeset(tset)
    for sent,autotaggedSent in zip(tset,autoTags):
        dtypes=[None for t in sent.tokens]
        for g,d,dType in sent.deps:
            if dtypes[d]==None or dTypeCounts.get(dType,0)>dTypeCounts.get(dtypes[d],0): #pick the most common type
                dtypes[d]=dType
        for i in range(len(dtypes)):
            if dtypes[i]==None:
                dtypes[i]=u"ROOT"
        for g,d,dType in sent.deps:
            if dtypes[d]==u"conj":
                dtypes[d]=dtypes[g] #TODO: check this bit
        for g,d,dType in sent.deps:
            if dType=="cop" and dtypes[g]:
                dtypes[g]=dtypes[g]+"_cop"
        for tidx,(token,autoreading) in enumerate(zip(sent.tokens,autotaggedSent)):
            readings=[]
            for cg,lemma,tags,other in token.posTags:
#                if not cg:
#                   continue
                pos,tags=pretty_format_taglist(tags)
                pos=u"POS_"+pos
                readings.append((pos,tags,lemma))
            (pos,tags,lemma),gType=resolve(token.text,readings,dtypes[tidx],autoreading)
            if len(readings)>1 or len(readings)==1 and readings[0][0]==u"POS_NON-TWOL":
                print u"*"*20
                if len(readings)==1 and readings[0][0]==u"POS_NON-TWOL":
                    print "NON-TWOL TRANSFER"
                print (u" ".join((ttt.text for ttt in sent.tokens[max(0,tidx-5):tidx+5]))).encode("utf-8")
                print
                print token.text.encode("utf-8"), dtypes[tidx], u"(",gType,u")"
                print ("%s %s %s"%(pos,tags,lemma)).encode("utf-8")
                print
                for r in readings:
                    print r
            token.resolvedPOS=(pos,tags,lemma)

def readDisambiguationData(fromFileName):
    global dTypeCounts,dTypePOSCounts,dTypeAllTagCounts,lemmaCounts
    f=open(fromFileName,"r")
    dTypeCounts,dTypeAllTagCounts,dTypePOSCounts,lemmaCounts=pickle.load(f)
    dTypePOSCounts[u"partmod"][u"POS_PCP1"]=1000 #forcing PCP1 over A
    dTypePOSCounts[u"ccomp"][u"POS_PCP1"]=dTypePOSCounts[u"ccomp"][u"POS_A"]+1 #forcing PCP1 over A
    dTypePOSCounts[u"iccomp"][u"POS_PCP1"]=dTypePOSCounts[u"iccomp"].get(u"POS_A",0)+1 #forcing PCP1 over A
    f.close()

def processTagList(lst,tagDict,prependCategory,wordform=u""):
    result={} #key: category, value: list of tags
    POS=None
    for tag in lst:
        if tag.startswith(u"<") and tag.endswith(u">"):
            tag=tag[1:-1]
        category=tagDict.get(tag)
        if not category:
            if tag.startswith(u"st-"):
                category=u"STYLE"
            elif tag.startswith("t-"):
                category=u"INFO"
            elif tag.startswith(u"DN-") or tag.startswith(u"DV-") or tag.startswith(u"DA-"):
                category=u"DERIV"
            else:
                warn("Warning: unknown tag "+tag+" in "+repr(lst)+" for "+wordform)
                category=u"OTHER"
        if category==u"POS": #treat POS separately
            if u"POS" in result: #already have a POS tag -> conflict
                if tag not in posPriority:
                    warn("Warning: choosing "+result[u"POS"][0]+" over "+tag)
                    result[u"POS"].append(tag) #...still want to preserve that tag, add it at the end
                elif result[u"POS"][0] not in posPriority or posPriority.index(tag)<posPriority.index(result[u"POS"][0]):
                    warn("dual POS: choosing "+tag+" over "+result[u"POS"][0])
                    result[u"POS"].insert(0,tag) #...still want to preserve that tag!
                else:
                    warn("Warning: choosing "+result[u"POS"][0]+" over "+tag)
                    result[u"POS"].append(tag) #...still want to preserve that tag, add it at the end
            else:
                result[u"POS"]=[tag]
        else:
            result.setdefault(category,[]).append(tag)
    if u"POS" not in result:
        warn("Warning: no POS in "+repr(lst)+" for "+wordform)
        result[u"POS"]=[u"UNK"]
    if len(result[u"POS"])>1:
        result[u"POS2"]=result[u"POS"][1:]
        result[u"POS"]=result[u"POS"][:1]
    return result
    

def readTagInfo(fName):
    tagDict={} #key: tag value: category
    f=codecs.open(fName,"rt","utf-8")
    for line in f:
        line=line.strip()
        if not line or line.startswith(u"#"):
            continue
        category,tag=line.split(u":")
        if tag in tagDict:
            warn(u"Warning: duplicate tag"+tag)
            continue
        tagDict[tag]=category
    f.close()
    return tagDict

taginfo=None #Cached dict
def parse_taglist(lst,wordform=u"<unspecified>"):
    """Input: list of unicode tags, output dictionary {category:[list of tags]} u"POS" category is always available - may be set to [u"UNK"], though"""
    global taginfo #dictionary produced by readTagInfo
    if taginfo==None:
        taginfo=readTagInfo(os.path.join(os.path.dirname(__file__),"twol_definitions"))
    tagDict=processTagList(lst,taginfo,wordform)
    for useless in [u"INFO",u"STYLE",u"OTHER"]:
        if useless in tagDict:
            del tagDict[useless]
    return tagDict

def pretty_format_taglist(lst,delimiter=u"|",wordform=u"<unspecified>"):
    d=parse_taglist(lst.split(),wordform)
    pos=d[u"POS"][0]
    res=[]
    for category in sorted(d):
        if category==u"POS":
            continue
        for tag in d[category]:
            res.append(category+"_"+tag)
    res.sort() #make sure we impose a proper order here
    return pos,delimiter.join(res)

if __name__=="__main__":
    w.simplefilter("ignore")
    from optparse import OptionParser
    parser = OptionParser(description="Interprets tags in the CoNLL-X files directly generated from TDT. 1) Identifies the main POS among the 4th column tags and puts it to the 3rd column 2) prefixes each tag with its category (see the tag_definitions file) 3) optionally drops certain tag categories (INFO,STYLE,OTHER by default). Reads stdin, writes stdout.")
    parser.add_option("-v", dest="verbose",action="store_true",default=False,help="Verbose debugging output")
    parser.add_option("--ignore", dest="ignore",action="store",default="INFO,STYLE,OTHER", help="Comma-separated list of categories to ignore. Defaults to 'INFO,STYLE,OTHER'.")
    parser.add_option("--no-category-prefix",dest="prependCategory",action="store_false",default=True,help="Do not prepend to each tag (e.g. SG -> NUMBER_SG) its category (default: do prepend)")

    parser.add_option("--buildstats",dest="buildstatsfile",action="store",default=None,help="Build POS disambiguation stats based on non-ambiguous cases. Give a directory with .d.xml files as first argument.")

    parser.add_option("--statsfile",dest="statsfile",action="store",default=None,help="POS disambiguation stats from --buildstats")
    parser.add_option("--retag",dest="retag",action="store",default=None,help="Retag a directory of .d.xmls")
    
    

    (options, args) = parser.parse_args()

    if options.buildstatsfile:
        gatherDepBasedStats(args[0], options.buildstatsfile)
        sys.exit()

    if options.statsfile:
        readDisambiguationData(options.statsfile)

    if options.retag:
        for fName in glob.glob(os.path.join(options.retag,"*.d.xml")):
            tset=dtreebank.core.treeset.TreeSet.fromFile(fName)
            retagTreeset(tset)
        sys.exit()


    assert False, "Must fix this first - the main function has changed"

    if options.verbose:
        w.simplefilter("once")


    dropCategories=set(unicode(options.ignore).split(u","))
    print >> sys.stderr, "Ignored categories:", unicode(dropCategories)
    tagDict=readTagInfo("tag_definitions")
    for line in sys.stdin:
        line=line.strip().decode("utf-8")
        if not line or line.startswith(u"#"):
            print line
            continue
        columns=line.split(u"\t")
        assert len(columns)==10
        tags=columns[3].split(u"|")
        POS,newTags=processTagList(tags,dropCategories,tagDict,options.prependCategory,columns[1])
        assert POS
        if not newTags:
            newTags=[u"_"]
        columns[3]=POS
        columns[4]=POS
        columns[5]=u"|".join(newTags)
        print (u"\t".join(columns)).encode("utf-8")


