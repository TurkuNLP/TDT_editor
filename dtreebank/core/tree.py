import datetime
import time
import sys
import os
import re

from dtreebank.gui import options

import xml.etree.cElementTree as ET
import dtreebank.cElementTreeUtils as ETUtils
import dtreebank.core.tree_functions as TF

try:
    from dtreebank.CG import py_fincg
    py_fincg.init()
    pyfinCG=True
    print >> sys.stderr, "CG Loaded"
except:
    pyfinCG=False
    

def PLEsc(str):
    return str.replace(u"'",ur"\'")

class Tree (object):
    """A single tree. A list of tokens and dependencies."""

    technicalDeps=set(("ellipsis","name","xsubj","xsubj-cop"))

    def __init__(self):
        self.text=None
        """Sentence text. Always a unicode string."""
        self.tokens=[]
        """A list of tokens in the tree, in their correct order."""
        self.deps={}
        """A set of dependencies in the tree, indexed by (g,d,type)."""
        self.eh=None
        """The EditHistory of this tree"""
        self.flags=[]
        """The flags of this tree - simply a list of strings"""
        self.treeset=None
        """The treeset which holds this sentence"""
        self.comments=[]

    def propBankTODO(self):
        reldeps=set()
        deps = {}
        #Look for red deps or CCSU deps or deps with type ?
        for dep in self.deps.itervalues():
            if u"flagged" in dep.flags or u"CCSU" in dep.flags \
                    or u"?" in dep.type:
                return True
            if dep.type==u"rel":
                reldeps.add(dep.dep)
            deps.setdefault(dep.dep,[]).append(dep.type)

        #rel with no second dep?
        for d in reldeps:
            assert u"rel" in deps[d]
            rels=0
            others=0
            for dep in deps[d]:
                if dep==u"rel":
                    rels+=1
                elif dep!=u"xsubj":
                    others+=1
            if rels!=others:
                return True

        return False

                
    def buildPOSTags(self):
        if not pyfinCG:
            return
        try:
            tokens=[tok.text for tok in self.tokens]
            resTW=py_fincg.analyzeTokens(tokens,False) #TWOL, tokenization
            resCG=py_fincg.analyzeTokens(tokens,True) #CG, tokenization
        except RuntimeError:
            return
        assert len(resTW)==len(self.tokens) and len(resCG)==len(self.tokens)
        for tIdx, (beg,end,readings) in enumerate(resTW):
            self.tokens[tIdx].posTags=[]
            cgRawTags=set(cgReading[1] for cgReading in resCG[tIdx][2])
            for base,rawTags,allTags in readings:
                self.tokens[tIdx].posTags.append([rawTags in cgRawTags,base,rawTags,allTags])

            


    def treeName(self): #used in the search window to identify where the tree comes from
        if self.treeset.fileName!=None:
            return os.path.basename(self.treeset.fileName)+u"/"+unicode(self.treeset.sentences.index(self)+1)
        else:
            return u"?/"+unicode(self.treeset.sentences.index(self)+1)
        
    def CCJumpDependency(self,(g,d,t),context=u"generic"):
        #Performs the CC-unfolding
        if (g,d,t) not in self.deps:
            return
        dep=self.deps[(g,d,t)]
        if t==u"conj":
            return #Refuse to cc-unfold a conj dependency!
        if u"CCE" in dep.flags:
            return #Refuse to cc-unfold an unfolded dependency
        if u"CCSU" not in dep.flags:
            return #Refuse to cc-unfold a dependency unless it has a CC-unconfirmed status
        #Figure out which end of the dependency jumps
        govJumps=[]
        depJumps=[]
        for g2,d2,t2 in self.deps.keys():
            if t2!=u"conj":
                continue
            #I have some other conj dependency
            if d==g2: #...its governor is dep's dependent -> dep jumps
                depJumps.append(d2)
            elif g==g2: #...its governor is dep's governor -> gov jumps
                govJumps.append(d2)
        unfolded=False
        for newG in govJumps:
            if (newG,d,t) in self.deps:
                continue
            newDep=Dep(newG,d,t,[f for f in dep.flags if not f.startswith(u"ARG")])#Remove all argument flags - we can't transfer argument safely across governors
            newDep.flags.remove(u"CCSU")
            newDep.flags.append(u"CCSC")
            newDep.flags.append(u"CCE")
            self.deps[(newG,d,t)]=newDep
            newDep.flags.sort()
            unfolded=True
        for newD in depJumps:
            if (g,newD,t) in self.deps:
                continue
            newDep=Dep(g,newD,t,dep.flags[:])
            newDep.flags.remove(u"CCSU")
            newDep.flags.append(u"CCSC")
            newDep.flags.append(u"CCE")
            self.deps[(g,newD,t)]=newDep
            newDep.flags.sort()
            unfolded=True
        if unfolded:
            dep.flags.remove(u"CCSU")
            dep.flags.append(u"CCSC")
            dep.flags.sort()
            self.hasChanged(context)

            
        
        

    def prologRep(self,plTsetIdx,plId):
        """plId is the numerical ID which this sentence will carry in the PL output.
        Returns a list of strings with the prolog statements. This is done so the output for the whole file can be
        sorted before printing and SWIPL does not complain."""
        outLines=[]
        for tIdx,t in enumerate(self.tokens):
            tokTxt=t.charOff2Str(self.text,t.charOff)
            outLines.append(u"token(%d,%d,%d,'%s')."%(plTsetIdx,plId,tIdx,PLEsc(tokTxt)))
        for dep in self.deps.values():
            outLines.append(u"dep(%d,%d,%d,%d,'%s')."%(plTsetIdx,plId,dep.gov,dep.dep,dep.type))
            argM=False
            argNum=False
            for tag in dep.flags:
                if tag.startswith(u"ARG"):
                    outLines.append(u"arg(%d,%d,%d,%d,'%s')."%(plTsetIdx,plId,dep.gov,dep.dep,PLEsc(tag)))
                    if tag.startswith(u"ARGM"):
                        argM=True
                    else:
                        argNum=True
                else:
                    outLines.append(u"flag(%d,%d,%d,%d,'%s')."%(plTsetIdx,plId,dep.gov,dep.dep,PLEsc(tag)))
            if argM and u"ARGM" not in dep.flags:
                outLines.append(u"arg(%d,%d,%d,%d,'ARGM-X')."%(plTsetIdx,plId,dep.gov,dep.dep)) #make ARGM if there was any ARGM-*, avoid duplication
            if argNum:
                outLines.append(u"arg(%d,%d,%d,%d,'ARGX')."%(plTsetIdx,plId,dep.gov,dep.dep)) #make ARGX if there was any ARG[0-9]
            
        for tIdx,token in enumerate(self.tokens):
            for cg,base,rawTags,allTags in token.posTags:
                outLines.append(u"twolreading(%d,%d,%d,'%s',[%s])."%(plTsetIdx,plId,tIdx,PLEsc(base),\
                                                                         u",".join(u"'"+PLEsc(tag)+u"'" for tag in rawTags.split())))
                if cg:
                    outLines.append(u"cgreading(%d,%d,%d,'%s',[%s])."%(plTsetIdx,plId,tIdx,PLEsc(base),\
                                                                         u",".join(u"'"+PLEsc(tag)+u"'" for tag in rawTags.split())))
            for tag in token.flags:
                hasSense=False
                if tag.startswith(u"SENSE"):
                    outLines.append(u"frame(%d,%d,%d,'%s')."%(plTsetIdx,plId,tIdx,tag[5:]))
                    hasSense=True
                if hasSense:
                    outLines.append(u"frame(%d,%d,%d,'X')."%(plTsetIdx,plId,tIdx))
                
#         if pyfinCG:
#             #Run the sentence through CG
#             txt=u" ".join(t.text for t in self.tokens)
#             res=py_fincg.analyzeSentence(txt,True,True) #CG, tokenization
#             assert len(res)==len(self.tokens)
#             for tIdx,(beg,end,readings) in enumerate(res):
#                 for base,rawTags,allTags in readings:
#                     outLines.append(u"cgreading(%d,%d,%d,'%s',[%s])."%(plTsetIdx,plId,tIdx,PLEsc(base),\
#                                                                          u",".join(u"'"+PLEsc(tag)+u"'" for tag in rawTags.split())))
#             res=py_fincg.analyzeSentence(txt,False,True) #TWOL, tokenization
#             assert len(res)==len(self.tokens)
#             for tIdx,(beg,end,readings) in enumerate(res):
#                 for base,rawTags,allTags in readings:
#                     outLines.append(u"twolreading(%d,%d,%d,'%s',[%s])."%(plTsetIdx,plId,tIdx,PLEsc(base),\
#                                                                          u",".join(u"'"+PLEsc(tag)+u"'" for tag in rawTags.split())))
        return outLines
                  
            
            

    def sanityProperties(self):
        isTree=True
        isComplete=False

        headCount=[0 for x in self.tokens]
        for g,d,t in self.deps.keys():
            if t in self.technicalDeps:
                continue
            headCount[d]+=1
        for g,d,t in self.deps.keys():
            if t=="name":
                if g>d:
                    beg,end=d,g
                else:
                    beg,end=g+1,d+1
                for tIdx in range(beg,end):
                    if headCount[tIdx]==0:
                        headCount[tIdx]=1
        for x in headCount:
            if x>1:
                isTree=False
        z=sum(1 for x in headCount if x==0)
        if z==0:
            isTree=False
        z=sum(headCount)
        if z==(len(self.tokens)-1):
            isComplete=True
### this doesn't work with names
#         ccCount,components=self.connectedComponents()
#         if ccCount>1:
#             isComplete=False
        return isTree,isComplete,[idx for idx in range(len(headCount)) if headCount[idx]==0]

    def hasChanged(self,context=u"generic"):
        self.treeset.treeChanged() #the context is really only interesting for the GUI at this point
    
    def editUnflagAllDeps(self,context=u"generic"):
        editList=[]
        for dep in self.deps.itervalues():
            if u"flagged" in dep.flags:
                editList.append((dep.gov,dep.dep,dep.type,"flagged"))
        if editList:
            self.editToggleFlag(editList,context)

    def deleteAllFlaggedDeps(self,tokens=None,context=u"generic"): #tokens is a list of tokens, keep at None to delete all flagged deps
        editList=[]
        for dep in self.deps.itervalues():
            if u"flagged" in dep.flags:
                if tokens==None or dep.gov in tokens or dep.dep in tokens:
                    editList.append((dep.gov,dep.dep,dep.type,None,None,None))
        if editList:
            self.editDepChange(editList,context)

    def editToggleFlag(self,editList,context=u"generic"):
        """ Provide a list of (G,D,Type,flagname) """
        edited=False
        for g,d,t,flagName in editList:
            dep=self.deps.get((g,d,t),None)
            if not dep:
                continue
            edited=True
            if flagName in dep.flags:
                dep.flags.remove(flagName)
                self.eh.toggleFlag((g,d,t,flagName,"-"))
            elif flagName.startswith(u"ARG"): #new arg - dump all other args from the flaglist
                dep.flags=[f for f in dep.flags if not f.startswith(u"ARG")]
                dep.flags.append(flagName)
                self.eh.toggleFlag((g,d,t,flagName,"+"))
            elif flagName.startswith(u"CCS"):
                if u"CCSU" in dep.flags:
                    dep.flags.remove(u"CCSU")
                    dep.flags.append(u"CCSC")
                elif u"CCSC" in dep.flags:
                    dep.flags.remove(u"CCSC")
                    dep.flags.append(u"CCSU")
                else:
                    dep.flags.append(u"CCSU")
            else:
                dep.flags.append(flagName)
                self.eh.toggleFlag((g,d,t,flagName,"+"))
            dep.flags.sort() #canonical order
        if edited:
            self.hasChanged(context)
                

    def editToggleTokenFlag(self,editList,context=u"generic"):
        """ Provide a list of (TokenIDX,flagname) """
        edited=False
        for tIdx,flagName in editList:
            token=self.tokens[tIdx]
            edited=True
            if flagName in token.flags:
                token.flags.remove(flagName)
                #self.eh.toggleFlag((g,d,t,flagName,"-"))
            else:
                if flagName.startswith(u"SENSE"):
                    token.flags=[f for f in token.flags if not f.startswith(u"SENSE")]
                token.flags.append(flagName)
                #self.eh.toggleFlag((g,d,t,flagName,"+"))
            token.flags.sort() #canonical order
        if edited:
            self.hasChanged(context)


    def editDepChange(self,editList,context=u"generic"):
        """ Provide a list of (oldG,oldD,oldType,newG,newD,newType)
        If you set oldG==oldD==oldType==None, you insert new dependency
        If you set newG==newD==newType==None, you delete an existing dependency
        If neither is None, you rewrite a dependency"""
        edited=False
        for oldG,oldD,oldType,newG,newD,newType in editList:
            editRecorded=False #since the edit can happen in two places, we must prevent it from being logged twice
            if oldG==newG and oldD==newD and oldType==newType:
                continue
            if newG!=None:
                assert newG!=newD and newType
                if (newG,newD,newType) not in self.deps:
                    dep=Dep(newG,newD,newType)
                    if newType in ("cophead","cophead:own"):
                        dep.flags=["L2"]
                    self.deps[(newG,newD,newType)]=dep
                    self.eh.depChange((oldG,oldD,oldType,newG,newD,newType))
                    editRecorded=True
                    edited=True
                else:
                    #the dependency is already there, do nothing
                    pass
            #Check sanity
            if oldG!=None:
                assert (oldG,oldD,oldType) in self.deps
                del self.deps[(oldG,oldD,oldType)]
                if not editRecorded:
                    self.eh.depChange((oldG,oldD,oldType,newG,newD,newType))
                edited=True
        if edited:
            self.hasChanged(context)

    def editAddNullToken(self,atIdx,context=u"generic"):
        newT=Token()
        if atIdx==0:
            newT.charOff=[(0,0)]
        else:
            prevEnds=self.tokens[atIdx-1].charOff[-1][-1]
            newT.charOff=[(prevEnds,prevEnds)]
        newT.text=Token.charOff2Str(self.text,newT.charOff)
        self.tokens[atIdx:atIdx]=[newT]
        newDeps={}
        for dep in self.deps.values():
            if dep.gov>=atIdx:
                dep.gov+=1
            if dep.dep>=atIdx:
                dep.dep+=1
            newDeps[(dep.gov,dep.dep,dep.type)]=dep
        self.deps=newDeps
        self.eh.addNullToken(atIdx)
        self.hasChanged(context)



    def editMergeToken(self,tokIdx,dir,context=u"generic",keep_head_pos=True):
        if dir==u"L" and tokIdx==0 or dir==u"R" and tokIdx==len(self.tokens)-1:
            return #can't do
        self.eh.mergeTokens(tokIdx,dir)
        #Implemented by first editing the other token to grow the text
        #and then deleting the current token
        if dir==u"L":
            self.tokens[tokIdx-1].charOff=Token.prettifyCharOff(self.tokens[tokIdx-1].charOff+self.tokens[tokIdx].charOff)
            self.tokens[tokIdx-1].text=Token.charOff2Str(self.text,self.tokens[tokIdx-1].charOff)
            self.tokens[tokIdx-1].posTags[0][1]+=self.tokens[tokIdx].posTags[0][1]
            if not keep_head_pos:
                self.tokens[tokIdx-1].posTags[0][0]=self.tokens[tokIdx].posTags[0][0]
                self.tokens[tokIdx-1].posTags[0][2]=self.tokens[tokIdx].posTags[0][2]
                self.tokens[tokIdx-1].posTags[0][3]=self.tokens[tokIdx].posTags[0][3]
        elif dir==u"R":
            self.tokens[tokIdx+1].charOff=Token.prettifyCharOff(self.tokens[tokIdx].charOff+self.tokens[tokIdx+1].charOff)
            self.tokens[tokIdx+1].text=Token.charOff2Str(self.text,self.tokens[tokIdx+1].charOff)
            self.tokens[tokIdx+1].posTags[0][1]=self.tokens[tokIdx].posTags[0][1]+self.tokens[tokIdx+1].posTags[0][1]
            if not keep_head_pos:
                self.tokens[tokIdx+1].posTags[0][0]=self.tokens[tokIdx].posTags[0][0]
                self.tokens[tokIdx+1].posTags[0][2]=self.tokens[tokIdx].posTags[0][2]
                self.tokens[tokIdx+1].posTags[0][3]=self.tokens[tokIdx].posTags[0][3]
        self.editDeleteToken(tokIdx,True,False) #True forces deletion of nonnull token here, False prevents the text to be touched
        #self.buildPOSTags()
        self.hasChanged(context)

    def editTokenText(self,tokIdx,newText,context=u"generic"):
        T=self.tokens[tokIdx]
        nullTok=T.isNull() #Are we replacing a null token?
#         if T.isNull(): #OK, we are turning a null token into a new token, must take some extra care!
#             return #UNIMPLEMENTED
        if len(T.charOff)>1: #Editing a multi-segment token... Noone should need this...
            return #UNIMPLEMENTED
        if T.isNull():
            oldLen=0
        else:
            oldLen=len(T.text)
        
        newLen=len(newText)
        B,E=T.charOff[0]
        if newLen==0: #Turning into a null token!
            T.text=u"*null*"
        else:
            T.text=newText
        if nullTok and B!=0 and not self.text[B-1].isspace(): #Replacing null token with no padding whitespace, add one
            crr=newLen-oldLen+1 #By this many characters I must move all offsets >=E
            self.text=self.text[:B]+u" "+newText+self.text[E:]
            T.charOff[0]=(B+1,B+1+len(newText))
        else: #Editing a standard token
            crr=newLen-oldLen #By this many characters I must move all offsets >=E
            self.text=self.text[:B]+newText+self.text[E:]
            T.charOff[0]=(B,B+len(newText))
        for T2 in self.tokens[tokIdx+1:]:
            T2.charOff=[(B+crr,E+crr) for B,E in T2.charOff]
        #Sanity
        for T in self.tokens:
            if T.isNull():
                continue
            assert T.text==Token.charOff2Str(self.text,T.charOff), (T.text,Token.charOff2Str(self.text,T.charOff))
        self.buildPOSTags()
        self.hasChanged(context)

    def editSplitToken(self,tokIdx,reference,context=u"generic"): #reference is the text of the token with one space
        reference=reference.strip() #split at beg. or end. makes no sense
        oldT=self.tokens[tokIdx]
        oldText=oldT.text
        if reference.replace(u" ",u"")!=oldText:
            return
        if reference.count(u" ")!=1:
            return

        splitIdx=reference.index(u" ")
        #splitIdx is index into the token text pointing to the char before which the split happens, but I need index into the sentence text!
        #kinda
        counter=0 #how many characters of the token have I seen so far?
        for B,E in oldT.charOff:
            spanLen=E-B
            if counter+spanLen<splitIdx: #this whole span goes before the split, move on
                counter+=spanLen
                continue
            else: #the hit is in this span
                splitIdxS=B+splitIdx-counter #translate splitIdx
                break
        else:
            assert False
        #now splitIdxS is an index into the sentence, not the token
        #now divide the char offsets between the old token and the new token
        #updatedCharOff is the list of spans for the orig token, to be updated
        #newCharOff is the list of spans for the new token, to be created after the orig token
        updatedCharOff=[]
        newCharOff=[]
        for B,E in oldT.charOff:
            if E<=splitIdxS:
                updatedCharOff.append((B,E))
            elif B>=splitIdxS:
                newCharOff.append((B,E))
            else: #split in this one!
                updatedCharOff.append((B,splitIdxS))
                newCharOff.append((splitIdxS,E))
        #Did all go well?
        assert Token.charOff2Str(self.text,oldT.charOff)==Token.charOff2Str(self.text,updatedCharOff)+Token.charOff2Str(self.text,newCharOff)
        newT=Token()
        newT.charOff=newCharOff
        newT.text=Token.charOff2Str(self.text,newT.charOff)
        oldT.charOff=updatedCharOff
        oldT.text=Token.charOff2Str(self.text,oldT.charOff)
        assert oldText==oldT.text+newT.text
        self.tokens[tokIdx:tokIdx+1]=[oldT,newT]
        newDeps={}
        for dep in self.deps.values():
            if dep.gov>=tokIdx+1:
                dep.gov+=1
            if dep.dep>=tokIdx+1:
                dep.dep+=1
            newDeps[(dep.gov,dep.dep,dep.type)]=dep
        self.deps=newDeps
        self.eh.splitToken(tokIdx,splitIdx)
        self.buildPOSTags()
        self.hasChanged(context)

    def editDeleteToken(self,atIdx,force=False,updateText=True,context=u"generic"):
        if not self.tokens[atIdx].isNull() and not force: #comment out to allow deletion of non-null tokens
            return
        delTok=self.tokens[atIdx]
        del self.tokens[atIdx]
        newDeps={}
        for dep in self.deps.values():
            if dep.gov==atIdx or dep.dep==atIdx:
                continue #this will essentially delete the dependency
            if dep.gov>atIdx:
                dep.gov-=1
            if dep.dep>atIdx:
                dep.dep-=1
            newDeps[(dep.gov,dep.dep,dep.type)]=dep
        self.deps=newDeps
        self.eh.deleteToken(atIdx)
        #Now one should yet update the text of the sentence!
        if not delTok.isNull() and updateText:
            delB,delE=delTok.charOff[0][0],delTok.charOff[-1][1] #delete the whole range
            if delB==0 and delE!=len(self.text) and self.text[delE]==" ":
                delE+=1 #first token takes its whitespace with itself
            elif delE==len(self.text) and delB!=0 and self.text[delB-1]==" ":
                delB-=1 #last token takes its whitespace
            elif delB!=0 and self.text[delB-1]==" " and delE!=len(self.text) and self.text[delE]==" ":
                delE+=1 #white-space surrounded token takes one space off
            delLen=delE-delB
            newText=self.text[:delB]+self.text[delE:]
            affFrom=delE
            #shift character offsets of all affected tokens 
            for t in self.tokens:
                newOff=[]
                for oldB,oldE in t.charOff:
                    if oldE<=affFrom:
                        newOff.append((oldB,oldE))
                    else:
                        assert oldB>=affFrom, ((oldB,oldE),affFrom)
                        newOff.append((oldB-delLen,oldE-delLen))
                assert Token.charOff2Str(self.text,t.charOff)==Token.charOff2Str(newText,newOff)==t.text, ( Token.charOff2Str(self.text,t.charOff),Token.charOff2Str(newText,newOff),t.text)
                t.charOff=newOff
            self.text=newText
        self.buildPOSTags()
        self.hasChanged(context)
            

    def editSplitSentence(self,atIdx,context=u"generic"):
        """Splits the sentence into two, ending this one just before token atIdx,
        and building and returning a new sentence from tokens starting atIdx.
        Dependencies between the two parts, if any, are discarded"""
        if atIdx==0: #No way splitting a sentence at its first word
            return
        newT=self.__class__() #make one of your own kind
        newT.tokens=self.tokens[atIdx:]
        newT.text=self.text[self.tokens[atIdx].charOff[0][0]:]
        #Also need to update new token character offsets!
        correction=self.tokens[atIdx].charOff[0][0] #this should be new offset 0
        for t in newT.tokens:
            t.charOff=[(B-correction,E-correction) for B,E in t.charOff]
            assert Token.charOff2Str(newT.text,t.charOff)==t.text
        self.tokens=self.tokens[:atIdx]
        self.text=self.text[:self.tokens[atIdx-1].charOff[-1][-1]]
        newT.flags=self.flags[:]
        newT.eh=EditHistory(ET.Element("edithistory"))
        for g,d,t in self.deps.keys():
            if g<atIdx and d<atIdx:
                continue #stays here
            elif g>=atIdx and d>=atIdx:
                #goes to the new sentence
                dep=self.deps[(g,d,t)]
                dep.gov-=atIdx
                dep.dep-=atIdx
                newT.deps[(g-atIdx,d-atIdx,t)]=dep
                del self.deps[(g,d,t)]
            else:
                #cross dependency!
                del self.deps[(g,d,t)]
        self.treeset.appendTreeAfter(self,newT)
        self.hasChanged(context)
        newT.hasChanged(context)

    def editAppendNextSentence(self,context=u"generic"):
        """Appends to this sentence the other sentence, and removes
        the other sentence from the treeset"""
        ownIdx=self.treeset.index(self)
        if ownIdx==len(self.treeset)-1:
            return
        other=self.treeset[ownIdx+1]
        off=len(self.text)+1 #1 for the extra space
        offToken=len(self.tokens) #number of own original tokens
        for t in other.tokens:
            #Add own length to all character offsets
            t.charOff=[(beg+off,end+off) for (beg,end) in t.charOff]
            self.tokens.append(t)
        self.text+=u" "+other.text
        #Add own length in tokens to the other sentence dependencies and insert them
        for dep in other.deps.itervalues():
            dep.gov+=offToken
            dep.dep+=offToken
            assert (dep.gov,dep.dep,dep.type) not in self.deps
            self.deps[(dep.gov,dep.dep,dep.type)]=dep
        self.treeset.deleteTree(other)
        self.hasChanged(context)
            

    def addDep(self,dep):
        if (dep.gov,dep.dep,dep.type) in self.deps:
            return False
        else:
            self.deps[(dep.gov,dep.dep,dep.type)]=dep

    def matchesToken(self,tokenExprRe):
        matches=[]
        for tIdx,t in enumerate(self.tokens):
            if tokenExprRe.match(t.text):
                matches.append(tIdx)
        return matches

    def matchesDependencyExt(self,govExprReObj,depExprReObj,typeExprReObj,direction,distinguishGD):
        matches=[]
        for g,d,dType in self.deps.keys():
            if direction=="L" and g<d or direction=="R" and g>d: #Failed direction?
                continue
            if typeExprReObj and not typeExprReObj.match(dType): #failed type
                continue
            if distinguishGD: #Check G/D
                if govExprReObj and not govExprReObj.match(self.tokens[g].text):
                    continue
                if depExprReObj and not depExprReObj.match(self.tokens[d].text):
                    continue
            else:
                if govExprReObj and (not govExprReObj.match(self.tokens[g].text) and not govExprReObj.match(self.tokens[d].text)):
                    continue
            #The dependency matches if you made it to here
            matches.append((g,d,dType))
        return matches

    def matchesDependency(self,tokenExprRe,depExprRe):
        #If tokenExprRe!=None, either the governor, or the dependent should match it
        matches=[]
        for g,d,dType in self.deps.keys():
            if depExprRe.match(dType):
                if tokenExprRe==None or tokenExprRe.match(self.tokens[g].text) or tokenExprRe.match(self.tokens[d].text):
                    matches.append((g,d,dType))
        return matches


    def editToggleSentenceFlag(self,flag,context=u"generic"):
        if flag=="grammaticality":
            #a three-state flag
            if "grammar-questionable" in self.flags:
                self.flags.remove("grammar-questionable")
                self.flags.append("ungrammatical")
            elif "ungrammatical" in self.flags:
                self.flags.remove("ungrammatical")
            else:
                self.flags.append("grammar-questionable")
        elif flag in self.flags:
            self.flags.remove(flag)
        else:
            self.flags.append(flag)
        self.flags.sort() #canonical order
        self.hasChanged(context)
        

    def getETTree(self):
        sNode=ET.Element("sentence")
        sNode.set("txt",self.text)
        if self.flags:
            sNode.set("flags",",".join(self.flags))
        for t in self.tokens:
            sNode.append(t.getETTree())
        
        #Try to output the dependencies in some sort of canonical order
        deps=self.deps.keys()
        deps.sort() #these are tuples, so they get sorted OK
        for d in deps:
            sNode.append(self.deps[d].getETTree())
        sNode.append(self.eh.getETTree())
        return sNode


    def asSvgElement(self,boldTokens=[],markFlagged=False,extendedSD=False,propbank=False,xargs=False,twol=False,cg=False,**kwargs):
        """
        boldTokens - list of token indices that should be bolded in the output
        markFlagged - mark flagged dependencies as red
        extendedSD - include dependencies with CCEXP flag (extended, CC-jumped dependencies)
        propbank - include arguments and frameset information, if found
        xargs - should xarg dependencies be included?
        """
        
        import dtreebank.draw_dg as draw_dg

        # Send all additional arguments straight to SVGOptions, 
        # this includes whAttributes so we don't need to handle it separately.
        for key in kwargs:
            setattr(draw_dg.SVGOptions,key,kwargs[key])
        
        svgTokens=[draw_dg.Token(t.text,idx) for idx,t in enumerate(self.tokens)]
        svgDeps=[]
        for dep in self.deps.itervalues():

            #if not exteded SD - ignore CCE and xsubj
            #ignore xargs unless specifically allowed
            if not extendedSD and (dep.type=="xsubj" or u"CCE" in dep.flags) or\
                    not xargs and dep.type==u"xarg":     
                continue

            depType=dep.type
            if propbank:
                #Search for propbank arguments
                for f in dep.flags:
                    if f.startswith(u"ARG"):
                        depType+=u":A"+f[3:]
                        break

            if dep.dep<dep.gov: #RL
                svgDeps.append(draw_dg.Dep(svgTokens[dep.dep],svgTokens[dep.gov],u"<"+depType))
            elif dep.dep>dep.gov: #LR
                svgDeps.append(draw_dg.Dep(svgTokens[dep.gov],svgTokens[dep.dep],depType+u">"))

            svgDep=svgDeps[-1] #what I just appended..

            #Flagging red
            if markFlagged and u"flagged" in dep.flags:
                svgDep.arcStyleDict["stroke"]="red"
                svgDep.labelStyleDict["fill"]="red"

            #Dashed CCEXP / xargs / xsubj
            if extendedSD and (u"CCE" in dep.flags or dep.type in (u"xarg",u"xsubj")):
                svgDep.arcStyleDict["stroke-dasharray"]="5,2"

        if propbank: #framesets of tokens
            for tokIdx,token in enumerate(self.tokens):
                for f in token.flags:
                    if f.startswith(u"SENSE"):
                        svgTokens[tokIdx].txt+=u"."+f[5:]

        #Attaching TWOL/CG analysis
        

        #Bolding tokens
        for tokIdx in boldTokens:
            svgTokens[tokIdx].styleDict["font-weight"]="bold"


        return draw_dg.generateSVG(svgTokens,svgDeps,title=self.text)

    @staticmethod
    def layer(d):
        if u"L1" in d.flags or u"L2" not in d.flags:
            return 1
        else:
            return 2
    @staticmethod
    def converted(d):
        if u"converted" in d.flags:
            return 1
        else:
            return 2

    @staticmethod
    def cmp_base_deps(d1,d2):
        d1_f=(Tree.layer(d1),Tree.converted(d1),d1.gov,d1.dep)
        d2_f=(Tree.layer(d2),Tree.converted(d2),d2.gov,d2.dep)
        return cmp(d1_f,d2_f)


    #0  1    2      3    4   5    6    7     8     9
    #id form lemma cpos pos feat head deprel deps misc
    def save_conllu(self,out):
        cols=[[u"_" for _ in range(10)] for _ in range(len(self.tokens))]
        for idx,t in enumerate(self.tokens):
            cols[idx][0]=unicode(idx+1)
            cols[idx][1]=t.text
            cols[idx][2]=t.posTags[0][1]
            tags=t.posTags[0][2].split(u"|",2)
            cols[idx][3]=tags[0].replace(u"CPOS_",u"")
            cols[idx][4]=tags[1].replace(u"POS_",u"")
            if len(tags)>2:
                assert len(tags)==3
                cols[idx][5]=tags[2]
            cols[idx][9]=t.misc
            cols[idx][6]=u"0"
            cols[idx][7]=u"root"
        converted_deps=[] #list of (gov,dep,dtype) -> converted dependencies to be highlighted
        #Gather the deps and sort
        heads=[[] for _ in range(len(self.tokens))]
        for (g,d,dtype),dep in self.deps.iteritems():
            heads[d].append(dep)
            if u"converted" in dep.flags:
                converted_deps.append((g+1,d+1,dtype))
        for idx,dheads in enumerate(heads):
            if not dheads:
                continue
            dheads.sort(cmp=self.cmp_base_deps)
            if u"L1" in dheads[0].flags or u"L2" not in dheads[0].flags:
                cols[idx][6]=unicode(dheads[0].gov+1)
                cols[idx][7]=dheads[0].type
                dheads=dheads[1:]
                 #..and now make sure the rest is in canonical order because it goes to the DEPS field
            if not dheads:
                continue
            dheads.sort(key=lambda d: (d.gov,d.type))
            cols[idx][8]=u"|".join(unicode(d.gov+1)+u":"+d.type for d in dheads)
        for g,d,t in converted_deps:
            print >> out, "#visual-style %d %d %s\tcolor:red"%(g,d,t)
        if self.comments:
            print >> out, (u"\n".join(self.comments)).encode("utf-8")
        self.eh.conllUComments(out)
        print >> out, (u"\n".join(u"\t".join(c) for c in cols)).encode("utf-8")
        print >> out


    def asSvgElementToFile(self, filename, **kwargs):
        """ 
        A quick wrapper to automatically save the tree's
        SVG representation to a file
        """
        import dtreebank.draw_dg as draw_dg
        svg = self.asSvgElement(**kwargs)
        draw_dg.writeUTF8(svg, filename)


    def ACC(self,gsTree):
        """Returns (number of tokens with correct head&type, number of tokens)"""
        this2gs,gs2this=self.alignTo(gsTree)
        #this2gs has all the tokens of this tree and stores index into gs, None if no correspondence
        #gs2this same thing, but the other way round
        #We now want to count the correct heads
        heads=[set() for x in self.tokens] #the set will contain (head,dType) pairs IN THE GS TREE INDEXING
        for g,d,t in self.deps:
            #Can I translate the head into the gs tree indexing?
            if this2gs[g]==None: #No! (token d is governed by a (null) token not present in the GS
                heads[d].add((None,None)) #Will add this head as (None,None) which will match nothing in the GS and render this token incorrect, which is what we'd like to see
            else: #The head has a correspondence in GS
                heads[d].add((this2gs[g],t))
        #So, a set with (None,None) as a member denotes a token which is headed by a (null) token in the GS tree
        #Now gather the heads in the GS tree
        gsHeads=[set() for x in gsTree.tokens]
        for g,d,t in gsTree.deps:
            gsHeads[d].add((g,t))


        #Done, so now I have the heads and need to check them against the GS
        correct=0
        for tIdx in range(len(self.tokens)):
            gsIdx=this2gs[tIdx]
            if gsIdx==None:
                continue #extra null, this one cannot be correct
            if heads[tIdx]==gsHeads[gsIdx]:
                correct+=1
        return correct,len(self.tokens)

    def betterCompareDepsTo(self,gsTree):
        this2gs,gs2this=self.alignTo(gsTree)
        res=set() #will hold (g,d,dType)
        correct=0
        correctHead=0
        correctType=0
        for g,d,dType in self.deps:
            gsG,gsD=this2gs[g],this2gs[d]
            if (gsG,gsD,dType) in gsTree.deps:
                correct+=1
                continue
            for gsg,gsd,gdType in gsTree.deps:
                if gsg==gsG and gsd==gsD:
                    correctHead+=1
                    break
                elif gsd==gsD and gdType==dType:
                    correctType+=1
                    break
        return correct,correctHead,correctType,len(self.deps)

    def compareDepsTo(self,gsTree):
        """Returns the set of dependencies which are incorrect in this tree"""
        this2gs,gs2this=self.alignTo(gsTree)
        res=set() #will hold (g,d,dType)
        
        for g,d,dType in self.deps:
            if (this2gs[g],this2gs[d],dType) not in gsTree.deps:
                res.add((g,d,dType))
        return res

    def wrongTokensSeq(self,gsTree):
        """Returns a sequence of True/False judgements against the given GS. Here False means heads are not right."""
        this2gs,gs2this=self.alignTo(gsTree)
        heads=[set() for x in self.tokens] #the set will contain (head,dType) pairs IN THE GS TREE INDEXING
        dependents=[set() for x in self.tokens]
        for g,d,t in self.deps:
            #Can I translate the head into the gs tree indexing?
            if this2gs[g]==None: #No! (token d is governed by a (null) token not present in the GS
                heads[d].add((None,None)) #Will add this head as (None,None) which will match nothing in the GS and render this token incorrect, which is what we'd like to see
            else: #The head has a correspondence in GS
                heads[d].add((this2gs[g],t))
            if this2gs[d]==None:
                dependents[g].add((None,None))
            else:
                dependents[g].add((this2gs[d],t))
        #So, a set with (None,None) as a member denotes a token which is headed by a (null) token in the GS tree
        #Now gather the heads in the GS tree
        gsHeads=[set() for x in gsTree.tokens]
        gsDeps=[set() for x in gsTree.tokens]
        for g,d,t in gsTree.deps:
            gsHeads[d].add((g,t))
            gsDeps[g].add((d,t))


        #Done, so now I have the heads and need to check them against the GS
        seq=[]
        for tIdx in range(len(self.tokens)):
            gsIdx=this2gs[tIdx]
            if gsIdx==None:
                seq.append(False)
                continue #extra null, this one cannot be correct
            if heads[tIdx]==gsHeads[gsIdx]:# and dependents[tIdx]==gsDeps[gsIdx]: #uncomment to get the deps as well
                seq.append(True)
            else:
                seq.append(False)
        assert len(seq)==len(self.tokens)
        return seq
        
                
    def alignTo(self,gsTree):
        """Calculates the this2gs and gs2this conversion of token indices"""
        #This gets complicated by the *nulls* -> the sentences to compare don't necessarily have the same number of tokens
        #we'll make two lists that translate the indices
        this2gs=[None for x in self.tokens] #index-to-index correspondence between tokens
        gs2this=[None for x in gsTree.tokens]
        thisIdx=0
        gsIdx=0
        while thisIdx<len(self.tokens) or gsIdx<len(gsTree.tokens):
            if thisIdx==len(self.tokens): #this sentence done
                assert gsTree.tokens[gsIdx].isNull()
                gsIdx+=1
                continue
            if gsIdx==len(gsTree.tokens): #gs sentence done
                assert self.tokens[thisIdx].isNull()
                thisIdx+=1
                continue
            #ok, we have two tokens to work with
            gTok=gsTree.tokens[gsIdx]
            tTok=self.tokens[thisIdx]
            if not (gTok.isNull() ^ tTok.isNull()): #^ is xor
                #both are null or non-null, we have a match!
                assert gTok.text==tTok.text
                this2gs[thisIdx]=gsIdx
                gs2this[gsIdx]=thisIdx
                thisIdx+=1
                gsIdx+=1
            elif gTok.isNull():
                assert not tTok.isNull()
                #So we have a null in the GS, but not in this sentence
                gsIdx+=1 #skip over it
            elif tTok.isNull():
                assert not gTok.isNull()
                #We have a null in this sentence, but not in GS
                thisIdx+=1
            else:
                assert False
        return this2gs,gs2this
        
        
    def connectedComponents(self):
        components=[None for x in self.tokens]
        edges={} #key: token value: set of tokens connected in the (undirected graph)
        for (g,d,t) in self.deps:
            edges.setdefault(g,set()).add(d)
            edges.setdefault(d,set()).add(g)
        ccCounter=0
        idx=0
        while idx<len(components):
            if components[idx]==None:
                ccCounter+=1
            self.DFS(idx,edges,ccCounter,components)
            idx+=1
        return ccCounter,components
        

    def DFS(self,tokenIdx,edges,ccNumber,components):
        if components[tokenIdx]!=None: #already visited
            return
        components[tokenIdx]=ccNumber
        for otherT in edges.get(tokenIdx,set()):
            self.DFS(otherT,edges,ccNumber,components)

    def fix_tree(self, steps="technicalOut,doubleGovsOut,connectIslands",paranoid=True):
        """Tries to fix the tree so that it passes is_correct_tree"""
        steps=steps.split(",")
        if "technicalOut" in steps:
            #remove known non-tree dependencies
            for (g,d,t),dep in self.deps.copy().iteritems():
                if t in self.technicalDeps-set(("name",)):
                    self.editDepChange([(g,d,t,None,None,None)])
                elif u"CCE" in dep.flags:
                    self.editDepChange([(g,d,t,None,None,None)])
                elif t!=u"rel" and (g,d,u"rel") in self.deps:
                    self.editDepChange([(g,d,t,None,None,None)])
        #connect names and clear anything under them.
            TF.link_dependencies(self,["name"])

        # find the current roots of the sentence
        roots=TF.find_islands(self).keys()

        #remove double govs
        #we introduce some logic here in choosing what to remove:
        #1) keep one dep where gov is in roots
        # This will fail on some weird circular systems,
        # since find_islands is not circular-safe. But
        # circles are bad anyways.
        if "doubleGovsOut" in steps:
            deps={}
            for (g,d,t) in self.deps.copy():
                deps.setdefault(d,[]).append((g,d,t))
            for lst in deps.values():
                lst.sort()
                if len(lst)==1:
                    continue
                conflTypes=set(t for g,d,t in lst)
                if u"rel" in conflTypes: #rel vs. something, take rel
                    self.editDepChange([(g,d,t,None,None,None) for (g,d,t) in lst if t!=u"rel"])
                    continue
                if u"gsubj" in conflTypes: #gsubj vs. something, take gsubj
                    self.editDepChange([(g,d,t,None,None,None) for (g,d,t) in lst if t!=u"gsubj"])
                    continue
                print >> sys.stderr, "Double gov", lst                            
                for idx,(g,d,t) in enumerate(lst):
                    if g in roots:
                        lst.append(lst.pop(idx))
                        break
                self.editDepChange([(g,d,t,None,None,None) for (g,d,t) in lst[:-1]])

        #if fixing names, ellipsis and double govs doesnt remove circularity
        #we can't tree-ify this tree
        if paranoid:
            assert not TF.find_circularity(self)

        #connect islands
        if "connectIslands" in steps:
            for i in roots[1:]:
                self.editDepChange([(None,None,None,roots[0],i,'dep')])


        #we either succeed or fail totally
        if paranoid:
            assert self.is_correct_tree()


    def is_correct_tree(self):
        """Returns true if the Tree is a correct tree"""
        deps={}
        for (g,d,t) in self.deps:
            if d in deps and t not in self.technicalDeps:
                return False
            if t not in self.technicalDeps:
                deps[d]=True
        return not TF.find_circularity(self) \
            and len(TF.find_islands(self))==1


class EditHistory (object):
    """The full edit history of the tree. With time stamps"""
    
    datetimeformat="%Y-%m-%d %H:%M:%S"

    def __init__(self,ehElem):
        """ehElem is the ET element that holds the history"""
        self.eh=ehElem
        try:
            import getpass
            self.user=getpass.getuser()
        except:
            self.user="unknown"
        self.totalEditTime=None
        self.readTotalEditTime()

    def isEmpty(self):
        return len(self.eh)==0

    def firstEdit(self):
        for elem in self.eh:
            tStamp=elem.get("time")
            if tStamp!=None:
                return tStamp
        return None

    def readTotalEditTime(self):
        self.totalEditTime=datetime.timedelta()
        for esElem in self.eh.getiterator("editsession"):
            beg,end=esElem.get("beg"),esElem.get("end")
            beg=datetime.datetime.strptime(beg,EditHistory.datetimeformat)
            end=datetime.datetime.strptime(end,EditHistory.datetimeformat)
            diff=end-beg
            self.totalEditTime+=diff

            
    def readLastEditTime(self):
        last = 0.0
        for esElem in self.eh.getiterator():
            if esElem.tag == 'depEdit' or esElem.tag == 'toggleFlag':
                if float(esElem.get("time")) > last:
                    last = float(esElem.get("time"))
        return last


    def getETTree(self):
        return self.eh

    def conllUComments(self,out):
        s=options.setup["history_suffix"]
        for e in self.eh.getiterator():
            if e.tag == 'depEdit':
                print >> out, "# EditHistory%s: (%s,%s,%s)->(%s,%s,%s)"%(s,e.get("oldG"),e.get("oldD"),e.get("oldT"),e.get("newG"),e.get("newD"),e.get("newT"))
            elif e.tag == 'toggleFlag':
                print >> out, "# ToggleFlag%s: (%s,%s,%s%s,%s)"%(s,e.get("G"),e.get("D"),e.get("T"),e.get("flag"),e.get("stat"))
            elif e.tag == 'editMerge':
                print >> out, "# MergeTokens%s: (%s,%s)"%(s,e.get("idx"),e.get("dir"))

    def recordEditSession(self,beg,end):
        diff=end-beg
        self.totalEditTime+=diff
        esElem=ET.SubElement(self.eh,"editsession")
        esElem.set("beg",beg.strftime(EditHistory.datetimeformat))
        esElem.set("end",end.strftime(EditHistory.datetimeformat))
        esElem.set("user",self.user)
        print esElem.get("beg"),"---",esElem.get("end")

    def mergeTokens(self,tIdx,dir):
        newEdit=ET.SubElement(self.eh,"editMerge")
        newEdit.set("idx",str(tIdx))
        newEdit.set("dir",dir)

    def depChange(self,edit):
        oldG,oldD,oldT,newG,newD,newT=edit
        newEdit=ET.SubElement(self.eh,"depEdit")
        newEdit.set("time",str(time.time()))
        newEdit.set("oldG",str(oldG))
        newEdit.set("oldD",str(oldD))
        newEdit.set("oldT",str(oldT))
        newEdit.set("newG",str(newG))
        newEdit.set("newD",str(newD))
        newEdit.set("newT",str(newT))
        newEdit.set("user",self.user)
        
    def addNullToken(self,atIdx):
        newEdit=ET.SubElement(self.eh,"addNull")
        newEdit.set("time",str(time.time()))
        newEdit.set("atIdx",str(atIdx))
        newEdit.set("user",self.user)
    
    def splitToken(self,tokIdx,charIdx):
        newEdit=ET.SubElement(self.eh,"splitToken")
        newEdit.set("time",str(time.time()))
        newEdit.set("tokIdx",str(tokIdx))
        newEdit.set("charIdx",str(charIdx))
        newEdit.set("user",self.user)


    def deleteToken(self,atIdx):
        newEdit=ET.SubElement(self.eh,"delToken")
        newEdit.set("time",str(time.time()))
        newEdit.set("atIdx",str(atIdx))
        newEdit.set("user",self.user)
    
    def toggleFlag(self,edit):
        G,D,T,Flag,NewStat=edit
        newEdit=ET.SubElement(self.eh,"toggleFlag")
        newEdit.set("time",str(time.time()))
        newEdit.set("G",str(G))
        newEdit.set("D",str(D))
        newEdit.set("T",str(T))
        newEdit.set("flag",str(Flag))
        newEdit.set("stat",NewStat)
        

    def timingCalibrationStats(self,actionTimes,idleTimes):
        #Do I have editsession
        lastTime=None
        editing=False
        if len(self.eh)>0 and self.eh[-1].tag=="editsession": #YES
            for e in self.eh:
                if e.tag=="editsession":
                    editing=False
                    continue
                newTime=float(e.get("time"))
                if editing:
                    if newTime-lastTime<1200:
                        actionTimes.append(newTime-lastTime)
                else:
                    if lastTime!=None:
                        if newTime-lastTime<1200:
                            idleTimes.append(newTime-lastTime)
                editing=True
                lastTime=newTime

    def hasEditSessions(self):
        return len(self.eh)>0 and self.eh[-1].tag=="editsession"

    def timeStats(self,sent,lastEditOfPrevious):
        """An attempt to study/check/visualize the time stats."""
        class TokenStat:
            
            def __init__(self):
                self.totalTime=0.0 #seconds
                self.depsInOut=0 #will be filled later
                self.isNull=False #only for checking purposes

        def atoi(x):
            if x=="None":
                return None
            else:
                return int(x)

        def distr(t1,t2,dType,timeDiff,tokenStats):
            if t1>t2:
                t1,t2=t2,t1
            if dType==u"name":
                affected=list(range(t1,t2+1))
            else:
                affected=[t1,t2]
            for x in affected:
                tokenStats[x].totalTime+=timeDiff/float(len(affected))

        totalProc,ignored=0,0 #how many edits do I process, how many do hit timeDiff>60?

        tokenStats=[TokenStat() for t in sent.tokens if not t.isNull()] #Init this to all non-null tokens
        falseDeps=set() #This will be used to check for consistency as I am replaying the edit history

        lastTime=lastEditOfPrevious
        for entry in self.eh:
            if entry.tag=="editsession":
                continue
            time=float(entry.get("time"))
            #now I know the time of this edit and 
            if lastTime==None:
                timeDelta=1 #FIX THIS LATER
            else:
                timeDelta=time-lastTime
                if timeDelta>60:
                    timeDelta=0 #ignore
                    ignored+=1
            totalProc+=1
            lastTime=time
            #ET.dump(entry)
            if entry.tag=="depEdit":
                newD,newG,newT,oldD,oldG,oldT=entry.get("newD"),entry.get("newG"),entry.get("newT"),entry.get("oldD"),entry.get("oldG"),entry.get("oldT")
                oldD=atoi(oldD)
                oldG=atoi(oldG)
                newD=atoi(newD)
                newG=atoi(newG)

                if oldD!=None:
                    assert oldG!=None and oldT!="None"
                    falseDeps.remove((oldG,oldD,oldT))
                if newD!=None:
                    assert newG!=None and newT!="None"
                    falseDeps.add((newG,newD,newT))
                #Distribute the time
                if oldD!=None and newD!=None:
                    distr(oldG,oldD,oldT,timeDelta/2,tokenStats)
                    distr(newG,newD,newT,timeDelta/2,tokenStats)
                elif oldD==None and newD!=None:
                    distr(newG,newD,newT,timeDelta,tokenStats)
                elif oldD!=None and newD==None:
                    #dep remove
                    distr(oldG,oldD,oldT,timeDelta,tokenStats)
                else:
                    assert False
                
                
            elif entry.tag=="addNull":
                atIdx=int(entry.get("atIdx"))
                tokenStats.insert(atIdx,TokenStat())
                tokenStats[atIdx].isNull=True
                newFalseDeps=set()
                for g,d,t in falseDeps:
                    if g>=atIdx:
                        g+=1
                    if d>=atIdx:
                        d+=1
                    newFalseDeps.add((g,d,t))
                falseDeps=newFalseDeps
            elif entry.tag=="delToken":
                atIdx=int(entry.get("atIdx"))
                del tokenStats[atIdx]
                newFalseDeps=set()
                for g,d,t in falseDeps:
                    if g==atIdx or d==atIdx:
                        continue
                    if g>atIdx:
                        g-=1
                    if d>atIdx:
                        d-=1
                    newFalseDeps.add((g,d,t))
                falseDeps=newFalseDeps
            elif entry.tag=="toggleFlag":
                d,g=int(entry.get("D")),int(entry.get("G"))
                tokenStats[d].totalTime+=timeDelta/2.0
                tokenStats[g].totalTime+=timeDelta/2.0
            
            
        #And now let's see that this all worked
        assert set(sent.deps.keys())==falseDeps, (sorted(sent.deps.keys()), sorted(falseDeps))
        assert len(tokenStats)==len(sent.tokens)
        for tStat,tok in zip(tokenStats,sent.tokens):
            assert tStat.isNull==tok.isNull()
        #Now normalize by the number of deps touching the token in the final annotation
        for g,d,t in falseDeps:
            tokenStats[g].depsInOut+=1
            tokenStats[d].depsInOut+=1
        for t in tokenStats:
            if t.depsInOut!=0: #tokens under "name" have nothing coming in/out, yet have valid time stats
                t.totalTime/=float(t.depsInOut)
        return tokenStats, time

    

class Token (object):
    """A single token"""
    
    def __init__(self):
        self.text=None
        """Text of the token. Always a unicode string."""
        self.charOff=[]
        """A list of (beg,end) pairs to mark the token in the text of the sentence. Interpreted as [beg:end] slice, so [beg:beg] means the token has no corresponding substring in the sentence text."""
        self.tags=set()
        """A set of tags (strings) for this token. The tags carry information about highlighting, etc. These are NOT TWOL tags."""
        self.flags=[]
        """Misc field in conllu"""
        self.misc=u"_"
        
        self.posTags=[]
        """A list of [CG?,base,rawTags,tagList] lists. CG? is True/False if the reading is chosen by CG, base is unicode string, rawTags is unicode string,tagList is a list of tags, some of which can be None"""

    def isNull(self):
        return len(self.charOff)==1 and self.charOff[0][0]==self.charOff[0][1]

    def getETTree(self):
        tNode=ET.Element("token")
#        tNode.set("start",unicode(self.charOff[0][0]))
#        tNode.set("end",unicode(self.charOff[0][1]))
        tNode.set("charOff",u",".join(unicode(B)+u"-"+unicode(E) for B,E in self.charOff))
        if self.flags:
            tNode.set("flags",unicode(u",".join(self.flags)))
        if self.posTags:
            for cg,base,rawtags,tagList in self.posTags:
                rNode=ET.SubElement(tNode,"posreading")
                if cg==True:
                    rNode.set("CG","true")
                elif cg==False:
                    rNode.set("CG","false")
                else:
                    rNode.set("CG","none")
                rNode.set("baseform",base)
                rNode.set("rawtags",rawtags)
                rNode.set("tags",u",".join(unicode(tag) for tag in tagList))
        return tNode

    @staticmethod
    def charOff2Str(sText,charOffsets):
        """Receives the sentence text and charoffsets and returns the text defined by these offsetss"""
        if len(charOffsets)==1 and charOffsets[0][0]==charOffsets[0][1]:
            return u"*null*"
        else:
            return u"".join(sText[b:e] for b,e in charOffsets)

    @staticmethod
    def prettifyCharOff(charOff): #merges offsets into disjoint blocks > [(0,3),(3,5),(7,8)] -> [(0,5),(7,8)]
        newOff=[charOff[0]]
        for B,E in charOff[1:]:
            if B==newOff[-1][1]:
                newOff[-1]=(newOff[-1][0],E)
            else:
                newOff.append((B,E))
        return newOff
        
        


class Dep (object):
    """A single dependency."""

    def __init__(self,gov,dep,type,flags=None):
        self.gov=gov
        """Governor. Token index."""
        self.dep=dep
        """Dependent. Token index."""
        self.type=type
        """Dependency type. A string."""
        if not flags:
            self.flags=[]
        else:
            self.flags=flags
        self.misc=u"_"
        """List of flags associated with this dependency"""
    
    def getETTree(self):
        dNode=ET.Element("dep")
        dNode.set("dep",unicode(self.dep))
        dNode.set("gov",unicode(self.gov))
        dNode.set("type",unicode(self.type))
        if self.flags:
            dNode.set("flags",unicode(",".join(self.flags)))
        return dNode




