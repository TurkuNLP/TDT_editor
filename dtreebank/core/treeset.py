import xml.etree.cElementTree as ET
import codecs
import traceback

import datetime
import time
import sys
import os

import dtreebank.cElementTreeUtils as ETUtils
import dtreebank.core.stanforddep as stanforddep
from dtreebank.core.tree import *

try:
    from dtreebank.CG import py_fincg
    py_fincg.init()
    pyfinCG=True
    print >> sys.stderr, "CG Loaded"
except:
    pyfinCG=False

def PLEsc(str):
    return str.replace(u"'",ur"\'")

def read_conllu(inp,maxsent=0):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as filename, otherwise as open file for reading in unicode"""
    if isinstance(inp,basestring):
        f=codecs.open(inp,u"rt",u"utf-8")
    else:
        f=codecs.getreader("utf-8")(sys.stdin) # read stdin
    count=0
    sent=[]
    comments=[]
    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,basestring):
        f.close() #Close it if you opened it


class TreeSet (object):
    """Model of an ordered list of trees, typically bound to a single file."""

    treeClass=Tree

    @classmethod
    def fromCONLLU(cls,inp,fileName=None):
        tset=cls()
        tset.fileName=fileName
        for sentence,comments in read_conllu(inp):
            tree=cls.treeClass()
            tree.comments=comments
            tree.eh=EditHistory(ET.Element("edithistory"))
            tree.treeset=tset
            tset.append(tree)
            currentoffset=0
            for cols in sentence:
                ID,FORM,LEMMA,CPOS,POS,FEAT,HEAD,DEPREL,DEPS,MISC=cols
                token=Token()
                token.charOff.append((currentoffset, currentoffset+len(FORM)))
                token.text=FORM
                tree.tokens.append(token)
                currentoffset+=len(FORM)+1
                tags=u"CPOS_"+CPOS+u"|"+u"POS_"+POS
                if FEAT!=u"_":
                    tags+=u"|"+FEAT
                post=[True,LEMMA,tags,[]]
                token.posTags.append(post)
                token.misc=MISC
            for cols in sentence:
                ID,FORM,LEMMA,CPOS,POS,FEAT,HEAD,DEPREL,DEPS,MISC=cols
                if HEAD==u"_":
                    continue
                dep=Dep(int(HEAD)-1,int(ID)-1,DEPREL)
                dep.flags=[u"L1"]
                if dep.type!=u"root":
                    tree.addDep(dep)
                if DEPS!=u"_" and DEPS:
                    for h_d in DEPS.split(u"|"):
                        h,d=h_d.split(u":",1)
                        dep=Dep(int(h)-1,int(ID)-1,d)
                        dep.flags=[u"L2"]
                        tree.addDep(dep)
            tree.text=u" ".join(t.text for t in tree.tokens)
        return tset


    @classmethod
    def fromFile(cls,fileName):
        #fileName is a Unicode object
        #TreeCls is the class of the Tree instances
        basename = os.path.basename(fileName).lower()
#         root, extension = os.path.splitext(basename)

#         if extension == u".dep":
#             # .dep for stanford dependency tree
#             return cls.fromStanfordDependency(fileName) #TODO
        if basename.endswith(".conll") or basename.endswith(".conllx") or basename.endswith(".conll09") or basename.endswith(".txt"):
            f=open(fileName)
            lines=f.readlines()
            f.close()
            return cls.fromCONLL(lines,fileName)
        elif basename.endswith(".conllu"):
            return cls.fromCONLLU(fileName,fileName)
        elif basename.endswith(".d.xml"):            
            ETtree=ET.parse(fileName).getroot()
            tset=cls.fromDXML(ETtree,fileName)
            return tset
        else:
            raise ValueError("Unrecognized file extension: "+fileName)


    @classmethod
    def fromCONLL(cls,lines,fileName=None):
        """Creates a new instance from a CoNLL-formated input (list of lines)"""
        tset=cls()
        tset.fileName=fileName #must remember to save as dxml though!
        currTree=None
        for line in lines:
            line=unicode(line,"utf-8").strip()
            if line.startswith(u"#"):
                continue
            elif not line:
                #Current tree done!
                currTree=None
                continue
            #Looks like a real input here...
            if currTree==None:
                    currTree=cls.treeClass()
                    currTree.eh=EditHistory(ET.Element("edithistory"))
                    currTree.text=u""
                    tset.appendTree(currTree)

            columns=line.split(u"\t")
            token=Token()
            currTree.tokens.append(token)
            if len(columns)==1: #Simple single-token line
                token.text=columns[0]
            elif len(columns) in (2,10,13,14):
                assert columns[0].isnumeric()
                token.text=columns[1]
            if token.text==u"*null*":
                #special treatment for this guy
                token.charOff=[(len(currTree.text),len(currTree.text))]
            else:
                if len(currTree.text)!=0:
                    currTree.text+=u" "
                token.charOff=[(len(currTree.text),len(currTree.text)+len(token.text))]
                currTree.text+=token.text
            #Now I have the token safely tucked in I hope, deal with POS
            if len(columns) in (10,13,14): #these are expected to have POS to start with
                if len(columns)==10: #Conll-X
                    lemma,pos,features=columns[2],columns[3],columns[5]
                    gov,dType=columns[6],columns[7]
                else: #Conll-09
                    lemma,pos,features=columns[2],columns[4],columns[6]
                    gov,dType=columns[8],columns[10]
                if lemma!=u"_":
                    token.posTags=[[True,lemma,u" ".join([pos]+features.split(u"|")),[None for x in range(15)]]]

                if gov not in (u"_",u"0"):
                    assert dType!=u"_"
                    gov=int(gov)-1
                    dep=len(currTree.tokens)-1
                    depObj=Dep(gov,dep,dType)
                    currTree.deps[(gov,dep,dType)]=depObj
        return tset
                    
            
            
        

    @classmethod
    def fromDXML(cls,dxmlTSet,fileName=None):
        """Creates a new instance from a parsed .d.xml treeset (parsed by cElementTree)"""
        tset=cls()
        tset.fileName=fileName
        tset.name=unicode(dxmlTSet.get("name"))
        tset.parseConfig=unicode(dxmlTSet.get("parseconfig"))
        for treeElem in dxmlTSet.getiterator("sentence"):
            tree=cls.treeClass()
            tset.appendTree(tree)
            tree.text=unicode(treeElem.get("txt"))
            treeFlags=treeElem.get("flags")
            if treeFlags!=None:
                tree.flags.extend(treeFlags.split(","))
            for tokenElem in treeElem.getiterator("token"):
                token=Token()
                B,E=tokenElem.get("start"),tokenElem.get("end")
                if B!=None and E!=None: #old style charoff
                    token.charOff.append((int(B),int(E)))
                else:
                    #new style charoff
                    segments=unicode(tokenElem.get("charOff")).split(u",")
                    token.charOff=[]
                    for s in segments:
                        if s.startswith(u"-1"):
                            s="0"+s[2:]
                            print >> sys.stderr, "Warning, spurious charOff",s
                        B,E=s.split(u"-")
                        token.charOff.append((int(B),int(E)))
                token.text=Token.charOff2Str(tree.text,token.charOff)
                flags=tokenElem.get("flags")
                if flags:
                    token.flags=unicode(flags).split(u",")
                for readingElem in tokenElem.getiterator("posreading"):
                    if unicode(readingElem.get("CG"))==u"true":
                        cg=True
                    elif unicode(readingElem.get("CG"))==u"false":
                        cg=False
                    else:
                        cg=None
                    tagList=unicode(readingElem.get("tags")).split(u",")
                    for idx in range(len(tagList)):
                        if tagList[idx]==u"None":
                            tagList[idx]=None
                    token.posTags.append([cg,unicode(readingElem.get("baseform")),unicode(readingElem.get("rawtags")),tagList])
                        
                tree.tokens.append(token)
            for depElem in treeElem.getiterator("dep"):
                flags=unicode(depElem.get("flags"))
                if not flags:
                    flags=[]
                else:
                    flags=flags.split(u",")
                dep=Dep(int(depElem.get("gov")),int(depElem.get("dep")),unicode(depElem.get("type")),flags)
                tree.addDep(dep)
            editHistoryElem=treeElem.find("./edithistory")
            if editHistoryElem!=None:
                tree.eh=EditHistory(editHistoryElem)
            else:
                tree.eh=EditHistory(ET.Element("edithistory"))
            #Do I need to rebuild the POS tags?
            # rerunCG=False
#             for t in tree.tokens:
#                 if len(t.posTags)>0:
#                     break #no!
#             else:
#                 #yes!
#                 rerunCG=True
#             if pyfinCG and rerunCG:
#                 tree.buildPOSTags()
        return tset

    @classmethod
    def fromStanfordDependency(cls,fileName):
        """Creates a new instance from a Stanford Dependency .dep file"""
        tset = cls()
        tset.fileName=fileName
        # TODO: how to set tset.name?
        sentences = stanforddep.readStanfordDependencySentences(fileName)
        for sentencedeps in sentences:
            # skip empties w/o comment
            if sentencedeps == []:
                continue

            tokens = stanforddep.tokensFromDependencies(sentencedeps, fileName)
            sentencetxt   = " ".join(tokens)

            # build the tree for this sentence
            tree=cls.treeClass()
            tset.appendTree(tree)
            tree.text=unicode(sentencetxt)
            currentoffset = 0
            for i, txt in enumerate(tokens):
                token=Token()
                token.charOff.append((currentoffset, currentoffset+len(txt)))
                token.text=unicode(txt)
                tree.tokens.append(token)
                currentoffset += len(txt)+1
            for deptype, headtxt, headidx, deptxt, depidx in sentencedeps:
                # silently ignore self-loops
                if depidx == headidx:
                    pass#continue
                # SD indexes from 1, adjust
                dep=Dep(headidx-1,depidx-1,unicode(deptype))
                tree.addDep(dep)
        return tset


    def prologRep(self,tsetIdx):
        outLines=[]
        for sIdx,s in enumerate(self.sentences):
            outLines.extend(s.prologRep(tsetIdx,sIdx))
        return outLines

    def prologRepStr(self,tsetIdx):
        lines=self.prologRep(tsetIdx)
        lines.sort() #so that prolog statements are grouped in the output
        return u"\n".join(lines)

    def __init__(self):
        self.fileName=None
        self.name=u""
        self.dirty=False
        self.sentences=[]
        self.currentTreeIdx=None #Holds a current position in the document, not saved in metadata
        self.parseConfig=None


    def __len__(self):
        return len(self.sentences)

    def __getitem__(self,k):
        return self.sentences[k]

    def __getattr__(self,aName):
        """Redirects all unknown method calls to self.sentences, this simulating multiple inheritance, which is not possible due to PyQT4 not implementing it"""
        return self.sentences.__getattribute__(aName)

    def appendTree(self,tree):
        self.append(tree)
        tree.treeset=self


    def appendTreeAfter(self,currentTree,newTree): #Called by a sentence when split into two
        idx=self.sentences.index(currentTree)
        self.sentences.insert(idx+1,newTree)
        newTree.treeset=self

    def deleteTree(self,tree): #Called by a sentence when merging sentences
        self.sentences.remove(tree)
        

    def treeChanged(self):
        self.dirty=True

    def save(self):
        if not self.fileName:
            raise ValueError("Cannot save unnamed treeset!")
        if self.fileName.lower().endswith(".d.xml"):
            root=self.getETTree()
            root.set("name",self.name)
            root.set("parseconfig",unicode(self.parseConfig))
            f=open(self.fileName,"wt")
            ETUtils.writeUTF8(root,f)
            f.close()
            self.dirty=False
        elif self.fileName.lower().endswith(".conllu"):
            out=open(self.fileName,"w")
            print >> sys.stderr, "Saving into", self.fileName+".bak"
            self.save_conllu(out)
            out.close()

    def save_conllu(self,out):
        for t in self.sentences:
            t.save_conllu(out)

    
    def getETTree(self):
        """Builds ET tree out of this treeset so it can be saved into a file"""
        root=ET.Element("treeset")
        for s in self.sentences:
            root.append(s.getETTree())
        return root

