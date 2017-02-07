from __future__ import division
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from dtreebank.iterableutils import argmax
from dtreebank.core.treeset import *
from dtreebank.core.tree import *
from dtreebank.gui.dtypedialog import *
import sys
import options as opt #TODO

argFlagKeys={Qt.Key_0:"0",
             Qt.Key_1:"1",
             Qt.Key_2:"2",
             Qt.Key_3:"3",
             Qt.Key_4:"4",
             Qt.Key_5:"5",
             Qt.Key_6:"6",
             Qt.Key_7:"7",
             Qt.Key_8:"8",
             Qt.Key_9:"9",
             Qt.Key_M:"M"}


class DTreeGraphicsView(QGraphicsView):
    
    def keyPressEvent(self,e):
        #Ignores all key events so the parent (DTreeWidget gets them)
        e.ignore()

    def setAlert(self,val):
        if val=="OK":
            self.scene().setBackgroundBrush(QColor.fromRgb(220,255,220,255))
        elif val=="ALERT":
            self.scene().setBackgroundBrush(QColor.fromRgb(255,220,220,255))
        else:
            self.scene().setBackgroundBrush(Qt.white)

    def sizeHint(self):
        br=self.scene().itemsBoundingRect() #would like to display the whole scene
        sh=QSize(int(br.width()),int(br.height()))
        return sh
        


class DTreeWidget(QWidget):
    """A widget for displaying and editing a single dependency tree."""

    def __init__(self,parent=None,context=u"generic",readOnly=False,fontSize=10):
        QWidget.__init__(self,parent)
        self.model=None
        """The tree we are working with"""

        self.preselectedTokens=set()
        """set of token indices -> these are selected after repaint"""
        self.preselectedDependencies=set()
        """set of (g,d,t) -> these dependencies are selected after repaint"""
        self.visualAlerts=opt.setup.get("treePaneAlert",True)
        """Should we display colored-background alerts to warn against non-treenes etc.?"""
        #self.vSpacing=15 # vspacing set in setFontSize 
        self.hSpacing=5

        self.buildGui()

        self.setFontSize(fontSize)

        self.contextMenuPolicy=Qt.DefaultContextMenu
        self.contextMenu=None
        self.context=context
        self.setContext(context)
        self.readOnly=readOnly #TODO - largely unsupported, keep this at False!
        self.connectedComponentLabels=[]

    def setFontSize(self,fontSize):
        fontSize=int(fontSize)
        # we need to calculate some numbers again.
        currentFont=QFont(self.font())
        currentFont.setBold(True)
        currentFont.setPointSize(fontSize)
        self.tokenBFM=QFontMetrics(currentFont) #Make the font metrics for bold font so we have enough space when selecting tokens and dependencies
        self.depBFM=QFontMetrics(currentFont)

        currentFont.setBold(False)
        self.setFont(currentFont)

        self.fontSize=fontSize

        self.vSpacing = self.depBFM.height()

        #gView
        self.gView.setFont(self.font())
        

    def setContext(self,context):
        self.context=context
        self.buildContextMenu(context)

    def buildContextMenu(self,context):
        if context==u"generic" or context==u"searchform":
            self.contextMenu=QMenu(self)
            self.contextMenu.addAction(u"Show in editor")
        elif context==u"editor":
            self.contextMenu=None
            

    def contextMenuEvent(self,ev):
        ev.accept()
        if self.contextMenu==None:
            return
        a=self.contextMenu.exec_(ev.globalPos())
        if a==None: #cancelled
            return
        if unicode(a.text())==u"Show in editor":
            self.emit(SIGNAL("gotoTreeObj(PyQt_PyObject)"),self.model)

    def sizeHint(self):
        sh=self.mainLayout.sizeHint()
        l,t,r,b=self.mainLayout.getContentsMargins()
        sh.setWidth(sh.width()+l+r+10)
        sh.setHeight(sh.height()+t+b+10)
        return sh

    def buildGui(self):
        self.gScene=QGraphicsScene() #Here is where we keep the scene with the various elements
        self.gView=DTreeGraphicsView(self.gScene,self) #Here is where we display the scene
        self.gView.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.flagLabel=None #here will be stored the widget with the label list (added/removed from the layout as needed)
        self.mainLayout=QVBoxLayout(self)
        self.mainLayout.addWidget(self.gView)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Minimum)

        self.tokenItems=[] #List of scene items corresponding to all tokens
        self.depItems={} #Dictionary of scene dependency items key:(gov,dep,type)

    def setModel(self,model,preselectedTokens=set(),preselectedDependencies=set()):
        """Sets a new model to be shown"""
        if self.model: #do I have a model existing?
            #stop listening
            QObject.disconnect(self.model.qtProxy,SIGNAL("treeChanged()"),self,SLOT("modelChanged()"))
        self.preselectedTokens=preselectedTokens
        self.preselectedDependencies=preselectedDependencies
        self.model=model
        #Should listen to the new model for any interesting changes
        self.connect(self.model.qtProxy,SIGNAL("treeChanged()"),SLOT("modelChanged()"))
        self.modelChanged()

    @pyqtSignature("")
    def modelChanged(self):
        """A slot that gets a message whenever the model changes (tokens/dependencies added/removed) and needs a repaint"""
        self.gScene=QGraphicsScene(self.gView) #make a new scene
        self.gScene.setFont(self.gView.font())
        self.populateScene()
        for tIdx in self.preselectedTokens:
            if tIdx >= 0 and tIdx<len(self.tokenItems):
                self.tokenItems[tIdx].setSelected(True)
        for g,d,t in self.preselectedDependencies:
            if (g,d,t) in self.depItems:
                self.depItems[(g,d,t)].setSelected(True)
                self.depItems[(g,d,t)].computeStyle()
                self.depItems[(g,d,t)].applyStyle()
        self.gView.setScene(self.gScene)
        isTree,isComplete,roots=self.model.sanityProperties()
        if self.visualAlerts:
            if not isTree:
                self.gView.setAlert("ALERT")
            elif isComplete:
                self.gView.setAlert("OK")
            else:
                self.gView.setAlert("NORMAL")
        #flags
        displayFlags=self.model.flags[:]
        if self.context in (u"searchform",):
            displayFlags.insert(0,self.model.treeName())
        if not displayFlags and self.flagLabel!=None:
            self.mainLayout.removeWidget(self.flagLabel)
            self.flagLabel.setParent(None)
            self.flagLabel.destroy()
            self.flagLabel=None
        elif displayFlags:
            if self.flagLabel==None:
                flagText=",".join(displayFlags)
                self.flagLabel=QLabel(flagText,self)
                self.mainLayout.insertWidget(0,self.flagLabel)
            else:
                self.flagLabel.setText(",".join(displayFlags))
        self.gView.updateGeometry()

    def populateScene(self):
        """Populate the scene with token/dependency items"""
        self.tokenContactXs,tokenBaseY=self.addTokens(self.hSpacing)
        self.addDeps(self.tokenContactXs,tokenBaseY,self.vSpacing)

    def getDTypeText(self,dep):
        res=dep.type
        for f in dep.flags:
            if f.startswith("ARG"):
                res+=u":A"+f[3:]
        return res

    def getTokenText(self,token):
        res=token.text
        for f in token.flags:
            if f.startswith(u"SENSE"):
                res+=u"."+f[5:]
        return res

    def addTokens(self,hSpacing):
        self.tokenItems=[]
        tokenContactXs=[]
        tokenYs=[]
        rightMar=0.0

        for tIdx,token in enumerate(self.model.tokens):
            txtItem=TokenItem(self.getTokenText(token),tIdx,self,tIdx==0,tIdx==len(self.model.tokens)-1,None,self.gScene)
            #Tooltip text
            if token.posTags:
                toolTipTxt=u""
                for cg,base,rawTags,allTags in token.posTags:
                    if cg:
                        toolTipTxt+=u"*"
                    else:
                        toolTipTxt+=u" "
                    toolTipTxt+="'"+base+"' "+rawTags+"\n"
                toolTipTxt=toolTipTxt[:-1]
                txtItem.setToolTip(toolTipTxt)
            self.tokenItems.append(txtItem)
            width=self.tokenBFM.width(self.getTokenText(token))

            #Now we need to figure out where to attach that token
            leftX=rightMar+hSpacing #Default position: current right margin of the text
            for (g,d,t),depObj in self.model.deps.items():
                if g==d: #special treatment for self-dependencies
                    if g!=len(self.model.tokens)-1:
                        d+=1
                    else:
                        g-=1
                if tIdx==max(g,d): #if the current token is a right-hand in some dependency
                    #...we want to make sure that dependency will have enough space to be drawn
                    minDepLen=self.depBFM.width(self.getDTypeText(depObj)+u">")+2*10+3 #width of dependency type+2*corner radius+2 pixels safety margin
                    leftX=max(leftX,tokenContactXs[min(g,d)]+minDepLen-width//2)
                    #So the leftX now is either its previous value, or a new value to accomodate that dependency
                    #whichever is larger
            contact=leftX+width//2+txtItem.boundingRect().left()
            tokenYs.append(txtItem.boundingRect().top())
            tokenContactXs.append(contact)
            txtItem.setPos(leftX,txtItem.y())
            rightMar=leftX+width
        return tokenContactXs,min(tokenYs)


    def addDeps(self,tokenContactXs,YBase,vSpacing):
        self.depItems={}
        deps=sorted(self.model.deps.values(),cmp=depCmp)
        #The layout algorithm for dependencies
        zBuffer=[0 for x in range(len(tokenContactXs)-1)]
        for d in deps:
            dStart,dEnd=d.gov,d.dep
            if dStart>dEnd:
                dType=u"<"+self.getDTypeText(d)
                dStart,dEnd=dEnd,dStart
            elif dStart<dEnd:
                dType=self.getDTypeText(d)+u">"
            else:
                dType=d.type
            if dStart!=dEnd: #not self-dependency, use standard algorithm
                height=max(zBuffer[dStart:dEnd])+1
                for idx in range(dStart,dEnd):
                    zBuffer[idx]=height
                startX=tokenContactXs[dStart]
                endX=tokenContactXs[dEnd]
            elif dStart==dEnd and dStart!=len(tokenContactXs)-1: #self dependency, not last token
                height=max(zBuffer[dStart:dEnd+1])+1
                for idx in range(dStart,dEnd+1):
                    zBuffer[idx]=height
                startX=tokenContactXs[dStart]
                endX=tokenContactXs[dEnd+1]
            elif dStart==dEnd and dStart==len(tokenContactXs)-1: #self dependency, last token
                height=1
                startX=tokenContactXs[dStart]
                endX=startX+60
            W=endX-startX
            depG=DepGItem(startX,YBase,W,height*vSpacing,dType,(d.gov,d.dep,d.type),d.flags,self,None,self.gScene)
            depG.setZValue(-height)
            self.depItems[(d.gov,d.dep,d.type)]=depG

    def showConnectedComponents(self):
        ccCount,components=self.model.connectedComponents()
        for tokIdx, component in enumerate(components):
            item=QGraphicsSimpleTextItem(str(component),None,self.gScene)
            x=self.tokenItems[tokIdx].x()
            y=self.tokenItems[tokIdx].y()-10
            item.setPos(x,y)





    #Edit logic starts here

    def clickOnDep(self,depItem,modifiers):
        """Called when a dependency is clicked (elsewhere than in a drag corner). Called directly by the dependency in its own mouse event handler"""
        if modifiers==Qt.NoModifier:
            #Unselect everything else
            for tokItem in self.tokenItems:
                tokItem.setSelected(False)
            for dep in self.depItems.values():
                if dep!=depItem:
                    dep.setSelected(False)
        depItem.toggleSelected()

    def clickOnToken(self,dtokItem,modifiers):
        """Called when a token is clicked"""
        if modifiers==Qt.ShiftModifier:
            #Do we have a token selected?
            for gtokItem in self.tokenItems:
                if gtokItem.isSelected: #yes
                    dialog=DTypeDialog(self)
                    if dialog.exec_()==QDialog.Accepted:
                        #keep the added dependency selected
                        self.preselectedDependencies=set(((gtokItem.id,dtokItem.id,dialog.selectedType),))
                        self.preselectedTokens=set((gtokItem.id,))
                        self.model.editDepChange([(None,None,None,gtokItem.id,dtokItem.id,dialog.selectedType)],self.context)
                    return
            else:
                return
        elif modifiers==Qt.NoModifier:
            for tokItem in self.tokenItems:
                if tokItem!=dtokItem:
                    tokItem.setSelected(False)
            for depItem in self.depItems.values():
                depItem.setSelected(False)
            dtokItem.toggleSelected()


    def closestToken(self,x):
        """Returns the index of the token closest to the given x coordinate"""
        dist,idx=argmax((abs(tcx-x) for tcx in self.tokenContactXs),reverse=True) #I want argmin really
        return idx

    def depCornerDrag(self,newPos,corner,depItem):
        """Called when a dependency corner is dragged"""
        #we need to see if this drag could be considered
        #as a dependency re-hanging. If yes, we edit the model
        #if not, we ignore
        gov,dep,type=depItem.id #this tells me which dependency was moved
        newTokIdx=self.closestToken(newPos.x())
        if (corner=="L" and gov<dep or corner=="R" and gov>dep) and gov!=newTokIdx: #governor moved
            self.regenPreselects()
            self.preselectedDependencies=set(((newTokIdx,dep,type),))
            self.model.editDepChange([(gov,dep,type,newTokIdx,dep,type)],self.context)
        elif (corner=="L" and dep<gov or corner=="R" and gov<dep) and dep!=newTokIdx: #dependent moved
            self.regenPreselects()
            self.preselectedDependencies=set(((gov,newTokIdx,type),))
            self.model.editDepChange([(gov,dep,type,gov,newTokIdx,type)],self.context)

    def regenPreselects(self):
        """Updates .preselectedTokens/Dependencies based on the current selection"""
        self.preselectedTokens=set()
        self.preselectedDependencies=set()
        for dep in self.depItems.values():
            if dep.getSelected():
                self.preselectedDependencies.add(dep.id)
        for tok in self.tokenItems:
            if tok.isSelected:
                self.preselectedTokens.add(tok.id)

    def allSelectedDeps(self):
        return [dep for dep in self.depItems.values() if dep.getSelected()]

    def allSelectedToks(self):
        return [tok for tok in self.tokenItems if tok.isSelected]


    def mergeToken(self,dtokItem,dir):
        """Called from a token, via context menu. dir is u"L" or u"R" """
        self.model.editMergeToken(dtokItem.id,dir,self.context)

    def editToken(self,dtokItem,newText):
        """Called from a token, via context menu."""
        self.model.editTokenText(dtokItem.id,newText,self.context)

    def editSentenceCutBefore(self,dtokItem):
        """Called from a token, via context menu."""
        self.model.editSplitSentence(dtokItem.id,self.context)

    def editSentenceAppendNext(self,dtokItem):
        """Called from a token, via context menu."""
        self.model.editAppendNextSentence(self.context)


    def splitToken(self,dtokItem,reference):
        """Called from a token, via context menu. reference is token text with a single space marking the split """
        self.model.editSplitToken(dtokItem.id,reference,self.context)
        

    #Keyboard events
    def keyPressEvent(self,e):
        PB=opt.setup.get("config")=="PB" #Config is "PropBank" -> allow the relevant actions
        if e.key()==Qt.Key_Delete:
            #gather all dependencies to be deleted
            editList=[] #list of (Gov,Dep,Type,None,None,None) tuples
            for dep in self.depItems.values():
                if dep.getSelected():
                    g,d,t=dep.id
                    editList.append((g,d,t,None,None,None))
            self.regenPreselects()
            self.preselectedDependencies=set()
            self.model.editDepChange(editList,self.context)
            for tok in self.tokenItems:
                if tok.isSelected:
                    self.preselectedTokens=set()
                    self.model.editDeleteToken(tok.id,context=self.context)
                    break
        elif e.key()==Qt.Key_Left:
            #All selected dependencies will turn left
            editList=[]
            for dep in self.depItems.values():
                if dep.getSelected():
                    g,d,t=dep.id
                    if g<d: #this dependency goes to right, turn it!
                        editList.append((g,d,t,d,g,t))
            self.regenPreselects()
            self.preselectedDependencies=set()
            for g,d,t,g2,d2,t2 in editList:
                self.preselectedDependencies.add((g2,d2,t2))

            self.model.editDepChange(editList,self.context)
        elif e.key()==Qt.Key_Right:
            #All selected dependencies will turn right
            editList=[]
            for dep in self.depItems.values():
                if dep.getSelected():
                    g,d,t=dep.id
                    if g>d: #this dependency goes to left, turn it!
                        editList.append((g,d,t,d,g,t))
            self.regenPreselects()
            self.preselectedDependencies=set()
            for g,d,t,g2,d2,t2 in editList:
                self.preselectedDependencies.add((g2,d2,t2))
            self.model.editDepChange(editList,self.context)
        elif e.key()==Qt.Key_Space:
            #Do I have at least one dependency selected?
            for dep in self.depItems.values():
                if dep.getSelected():
                    break
            else:
                return
            dialog=DTypeDialog(self)
            if dialog.exec_()==QDialog.Accepted:
                editList=[]
                for dep in self.depItems.values():
                    if dep.getSelected():
                        g,d,t=dep.id
                        editList.append((g,d,t,g,d,dialog.selectedType))
                self.regenPreselects()
                self.preselectedDependencies=set()
                for g,d,t,g2,d2,t2 in editList:
                    self.preselectedDependencies.add((g2,d2,t2))
                self.model.editDepChange(editList,self.context)
        elif e.key()==Qt.Key_Exclam or e.key()==Qt.Key_F:
            #Do I have at least one dependency selected?
            for dep in self.depItems.values():
                if dep.getSelected():
                    break
            else:
                return
            editList=[]
            for dep in self.depItems.values():
                if not dep.getSelected():
                    continue
                g,d,t=dep.id
                editList.append((g,d,t,u"flagged"))
            self.regenPreselects()
            for g,d,t,f in editList:
                self.preselectedDependencies.add((g,d,t))
            self.model.editToggleFlag(editList,self.context)
        elif PB and e.modifiers()==Qt.NoModifier and e.key() in argFlagKeys:
            k=argFlagKeys[e.key()]            
            #Do I have at least one dependency selected?
            selectedDeps=self.allSelectedDeps()
            selectedToks=self.allSelectedToks()
            if selectedDeps:
                editList=[]
                for dep in selectedDeps:
                    g,d,t=dep.id
                    editList.append((g,d,t,u"ARG"+k))
                self.regenPreselects()
                for g,d,t,f in editList:
                    self.preselectedDependencies.add((g,d,t))
                self.model.editToggleFlag(editList,self.context)
            elif selectedToks:
                editList=[]
                for tok in selectedToks:
                    editList.append((tok.id,u"SENSE"+k))
                self.regenPreselects()
                self.model.editToggleTokenFlag(editList,self.context)
        elif PB and ((e.modifiers()==Qt.ShiftModifier and e.key()==Qt.Key_M) or e.key()==Qt.Key_A):
            #Ask for ArgM
            selectedDeps=self.allSelectedDeps()
            if selectedDeps:
                dialog=DTypeDialog(self,"argmtypes",3)
                if dialog.exec_()==QDialog.Accepted:
                    editList=[]
                    for dep in selectedDeps:
                        g,d,t=dep.id
                        editList.append((g,d,t,u"ARGM-"+dialog.selectedType))
                    self.regenPreselects()
                    self.model.editToggleFlag(editList,self.context)
        elif PB and e.key()==Qt.Key_C: #Flip the ConjConfirm tri-state flag CCS*
            selectedDeps=self.allSelectedDeps()
            if selectedDeps:
                editList=[]
                for dep in selectedDeps:
                    g,d,t=dep.id
                    editList.append((g,d,t,u"CCS"))
                self.regenPreselects()
                self.model.editToggleFlag(editList,self.context)
        elif PB and e.key()==Qt.Key_E: #Flip the "is conj-expanded flag" CCE
            selectedDeps=self.allSelectedDeps()
            if selectedDeps:
                editList=[]
                for dep in selectedDeps:
                    g,d,t=dep.id
                    editList.append((g,d,t,u"CCE"))
                self.regenPreselects()
                self.model.editToggleFlag(editList,self.context)
        elif e.key()==Qt.Key_2: #Flip the dep into the 2nd layer
            selectedDeps=self.allSelectedDeps()
            if selectedDeps:
                editList=[]
                for dep in selectedDeps:
                    g,d,t=dep.id
                    editList.append((g,d,t,u"layer"))
                self.regenPreselects()
                self.model.editToggleFlag(editList,self.context)
        elif PB and e.key()==Qt.Key_J: #Jump conj
            selectedDeps=self.allSelectedDeps()
            if selectedDeps:
                self.regenPreselects()
                self.model.CCJumpDependency(selectedDeps[0].id,self.context)
        elif e.key()==Qt.Key_Question:
            self.model.editToggleSentenceFlag("grammaticality",self.context)
        elif e.key()==Qt.Key_Insert:
            for tokItem in self.tokenItems:
                if tokItem.isSelected:
                    self.regenPreselects()
                    if e.modifiers()==Qt.ShiftModifier:
                        self.model.editAddNullToken(tokItem.id+1,self.context)
                    else:
                        self.model.editAddNullToken(tokItem.id,self.context)
                    self.preselectedDependencies=set()
                    self.preselectedTokens=set((tokItem.id,))
                    break
        elif e.key()==Qt.Key_X:
            lst=[]
            for tokItem in self.tokenItems:
                if tokItem.isSelected:
                    lst.append(tokItem.id)
            if lst:
                self.regenPreselects()
                self.model.deleteAllFlaggedDeps(lst,self.context)
        elif e.key()==Qt.Key_I:
            self.showConnectedComponents()
        # we ignore the fontsize change commands and let a parent handle it.
        elif e.key()==Qt.Key_Plus:
            e.ignore()
        elif e.key()==Qt.Key_Minus:
            e.ignore()

                
class TokenItem(QGraphicsSimpleTextItem):
    """Graphics item for a single token, held in the scene"""

    def __init__(self,text,id,dtWidget,firstToken,lastToken,parent=None,scene=None):
        QGraphicsSimpleTextItem.__init__(self,text,parent,scene)
        self.setFont(self.scene().font())
        self.id=id #holds the index of the token
        self.dtWidget=dtWidget
        self.isSelected=False
        self.contextMenuPolicy=Qt.DefaultContextMenu
        self.contextMenu=None
        if opt.setup["textEdit"]:
            self.contextMenu=QMenu(None)
            a=self.contextMenu.addAction(u"Merge left")
            if firstToken:
                a.setDisabled(True)
            a=self.contextMenu.addAction(u"Merge right")
            if lastToken:
                a.setDisabled(True)
            self.contextMenu.addAction(u"Split token...")
            self.contextMenu.addAction(u"Edit...")
            self.contextMenu.addAction(u"New sent from here")
            a=self.contextMenu.addAction(u"Append following sent")
            if not lastToken:
                a.setDisabled(True)
        self.text=text

#        self.defineActions()

#     def defineActions(self):
#         mergeLeftA = QAction("Merge left",None)
#         Qt.connect(mergeLeftA, SIGNAL(triggered()), self, SLOT(mergeLeft()))
#         self.addAction(mergeLeftA);

    def contextMenuEvent(self,ev):
        ev.accept()
        if self.dtWidget.readOnly:
            return
        if self.contextMenu==None:
            return
        a=self.contextMenu.exec_(ev.screenPos())
        if a==None: #cancelled
            return
        if unicode(a.text())==u"Merge left":
            self.dtWidget.mergeToken(self,u"L")
        elif unicode(a.text())==u"Merge right":
            self.dtWidget.mergeToken(self,u"R")
        elif unicode(a.text())==u"Split token...":
            txt,ok=QInputDialog.getText(self.dtWidget,u"Token split",u"Mark the position of the split by inserting a single space",QLineEdit.Normal,self.text)
            if txt==None or txt=="" or ok==False:
                return
            self.dtWidget.splitToken(self,unicode(txt))
        elif unicode(a.text())==u"Edit...":
            txt,ok=QInputDialog.getText(self.dtWidget,u"Token text edit",u"Give a new text for the token (must not contain spaces)",QLineEdit.Normal,self.text)
            if txt==None or ok==False:
                return
            txt=unicode(txt)
            if u" " in txt:
                return
            self.dtWidget.editToken(self,txt)
        elif unicode(a.text())==u"New sent from here":
            self.dtWidget.editSentenceCutBefore(self)
        elif unicode(a.text())==u"Append following sent":
            self.dtWidget.editSentenceAppendNext(self)
        else:
            assert False, a.text()

    def shape(self):
        return QGraphicsItem.shape(self) #use the default implementation which uses the bounding region

    def computeStyle(self):
        self.textFont=self.scene().font()
        self.textBrush=QBrush(Qt.SolidPattern)
        self.textBrush.setColor(Qt.black)

        if self.isSelected: #A selected dependency is bold all-through
            self.textFont.setBold(True)

    def applyStyle(self):
        self.setFont(self.textFont)
        self.setBrush(self.textBrush)


    def setSelected(self,v):
        self.isSelected=v
        self.computeStyle()
        self.applyStyle()

    def toggleSelected(self):
        self.setSelected(not self.isSelected)

    def contains(self,p):
        return self.boundingRect().contains(p)

    def boundingRect(self):
        r=QGraphicsSimpleTextItem.boundingRect(self)
        if r.width()>=15:
            return r
        else:
            PAD=int(15-r.width())//2
            return QRectF(r.left()-PAD,r.top(),r.width()+2*PAD,r.height())

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            self.dtWidget.clickOnToken(self,e.modifiers())
#         elif e.button()==Qt.RightButton:
#             self.dtWidget.rclickOnToken(self,e.modifiers())


def depCmp(a,b):
    """Sort of dependencies for the purpose of layout. First by length, then by left token"""
    aLen=abs(a.gov-a.dep)        
    bLen=abs(b.gov-b.dep)
    if aLen!=bLen:
        return cmp(aLen,bLen)
    aStart=min(a.gov,a.dep)
    bStart=min(b.gov,b.dep)
    return cmp(aStart,bStart)


class DepGItem (QGraphicsItem):
    """Item for a single dependency, built as a group of individual lines, arcs, label, etc..."""

    def __init__(self,X,Y,W,H,dType,id,flags,dtWidget,parent=None,scene=None):
        QGraphicsItem.__init__(self,parent,scene)
        self.id=id
        """Whatever ID one wants to associate with this item. Typically (gov,dep,type) tuple."""
        self.X=X
        """X-coordinate of the left corner"""
        self.Y=Y
        """Y-coordinate of the left corner"""
        self.W=W
        """Width in pixels"""
        self.H=H
        """Height in pixels"""
        self.dType=dType
        """The dependency type"""
        self.flags=flags
        """The flags of the dependency"""
        self.RAD=10  #Corner radius
        
        self.dtWidget=dtWidget

        self.tText=None

        self.itemSelected=False
        self.computeStyle()

        currentFont=QFont(scene.font())
        currentFont.setBold(True)
        self.depBFM=QFontMetrics(currentFont)

        self.build()

        self.applyStyle()

        self.shapeCache=None
        """Does this dependency react to mouse-over, allowing resizing?"""
        self.resizable=True
        self.setHandlesChildEvents(True)
        self.setAcceptsHoverEvents(True)
        self.dragState=None #




    def computeStyle(self):
        """self.tags is a list of text tags which are part of the annotation (unlike select/unselect).
        Currently the "red-flagging" is supported"""

        self.typeFont=self.scene().font()
        self.typeBrush=QBrush(Qt.SolidPattern)
        self.typeBrush.setColor(Qt.black)

        self.lineBrush=QBrush(Qt.SolidPattern)
        self.linePen=QPen()

        if self.getSelected(): #A selected dependency is bold all-through
            self.typeFont.setBold(True)
            self.linePen.setWidth(2)

        if u"flagged" in self.flags: #A flagged dependency is red
            self.lineBrush.setColor(Qt.red)
            self.typeBrush.setColor(Qt.red)

        if u"CCSU" in self.flags:
            self.lineBrush.setColor(Qt.blue)
            if u"flagged" not in self.flags:
                self.typeBrush.setColor(Qt.blue)

        if u"CCSC" in self.flags:
            self.lineBrush.setColor(Qt.green)
            if u"flagged" not in self.flags:
                self.typeBrush.setColor(Qt.green)

        if u"CCE" in self.flags:
            self.linePen.setDashPattern([3,3])
            
        if u"L2" in self.flags:
            self.linePen.setDashPattern([3,3])
            self.lineBrush.setColor(Qt.blue)
            self.typeBrush.setColor(Qt.blue)
        
        self.linePen.setBrush(self.lineBrush)

    def applyStyle(self):
        self.tText.setFont(self.typeFont)
        self.tText.setBrush(self.typeBrush)
        if self.hLineL:
            self.hLineL.setPen(self.linePen)
        if self.hLineR:
            self.hLineR.setPen(self.linePen)
        self.lCorner.setPen(self.linePen)
        


    def isCorner(self,point):
        """Is the point over a corner for dragging? And if so, which one: "L", "R", or None"""
        if self.lCorner.contains(point):
            return "L"
        if self.rCorner.contains(point):
            return "R"
        return None

    def mouseMoveEvent(self,e):
        pass

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            c=self.isCorner(e.pos())
            if c:
                #We have a press on corner - initiate moving
                assert self.dragState==None
                self.dragState=(c,e.pos())
            else:
                self.dtWidget.clickOnDep(self,e.modifiers()) #select?

    def mouseReleaseEvent(self,e):
        if self.dragState:
            #The user has dragged the edge
            newPos=e.scenePos()
            corner=self.dragState[0]
            self.dragState=None
            #Inform the parent
            self.dtWidget.depCornerDrag(newPos,corner,self)

    def shape(self):
        """Shape, to allow more precise selection"""
        PAD=2
        W=self.W
        H=self.H
        if self.shapeCache!=None:
            return self.shapeCache
        s=QPainterPath()
        pol=QPolygonF()
        #OUTER SHAPE CLOCKWISE
        pol.append(QPointF(-PAD,PAD))
        pol.append(QPointF(-PAD,-H-PAD))
        pol.append(QPointF(W+PAD,-H-PAD))
        pol.append(QPointF(W+PAD,PAD))

        #INNER SHAPE COUNTERCLOCKWISE
        pol.append(QPointF(W-PAD,PAD))
        pol.append(QPointF(W-PAD,-H+self.RAD)) 
        pol.append(QPointF(W-self.RAD,-H+PAD))
        pol.append(QPointF(self.RAD,-H+PAD))
        pol.append(QPointF(PAD,-H+self.RAD))
        pol.append(QPointF(PAD,PAD))

        s.addPolygon(pol)
        s.closeSubpath()
        self.shapeCache=s
        return self.shapeCache

    def build(self):
        """Builds itself (creates group items for the line, label, etc)"""
        g,d,t=self.id
        RAD=self.RAD
        #Text label
        self.tText=QGraphicsSimpleTextItem(self.dType,self)
        self.tText.setFont(self.scene().font())
        bRect=self.tText.boundingRect()
        dTypeWidth=bRect.width()#self.depBFM.width(self.dType)+2
        #move the text to half dep. width minus half text width and dep. height - half text height

        self.tText.setPos(self.W//2-dTypeWidth//2,-self.H-bRect.height()//2)
        #Left vertical line
        vLineLeft=QGraphicsLineItem(0,0,0,-self.H+RAD,self)
        #Right vertical line
        if g!=d:
            vLineRight=QGraphicsLineItem(self.W,0,self.W,-self.H+RAD,self)
        #Horizontal line
        #left half:
        startPointX=RAD
        endPointX=self.W//2-dTypeWidth//2
        if endPointX>startPointX:
            self.hLineL=QGraphicsLineItem(RAD,-self.H,endPointX,-self.H,self)
        else:
            self.hLineL=None
        startPointX=self.W//2+dTypeWidth//2
        endPointX=self.W-RAD
        if endPointX>startPointX and g!=d:
            self.hLineR=QGraphicsLineItem(startPointX,-self.H,endPointX,-self.H,self)
        else:
            self.hLineR=None

        #Left corner
        self.lCorner=ArcItem(RAD,-self.H+RAD,RAD,"L",self)
        self.lCorner.setCursor(Qt.SizeHorCursor)
        self.lCorner.setAcceptsHoverEvents(True)
        #Right corner
        if g!=d:
            self.rCorner=ArcItem(self.W-RAD,-self.H+RAD,RAD,"R",self)
            self.rCorner.setCursor(Qt.SizeHorCursor)
            self.rCorner.setAcceptsHoverEvents(True)
        else:
            self.rCorner=None
        self.setPos(self.X,self.Y)

    def getSelected(self):
        return self.itemSelected
    
    def setSelected(self,v):
        self.itemSelected=v
        self.computeStyle()
        self.applyStyle()
#         brush=self.tText.brush()
#         if self.isSelected:
#             brush.setColor(Qt.red)
#         else:
#             brush.setColor(Qt.black)
#         self.tText.setBrush(brush)

    def toggleSelected(self):
        self.setSelected(not self.getSelected())


    def boundingRect(self):
        width=self.W
        height=self.H+self.tText.boundingRect().height()//2+1
        return QRectF(0,-height,width,height)

    def paint(self,painter,option,widget):
        #No own painting to do
        pass


class ArcItem (QAbstractGraphicsShapeItem):
    """Graphics item: single arc"""
    
    def __init__(self,x,y,r,corner,parent=None,scene=None):
        """center, radius, "L" or "R" for left/right corner."""
        QAbstractGraphicsShapeItem.__init__(self,parent,scene)
        self.x=x
        self.y=y
        self.r=r
        self.corner=corner
        if self.corner=="L":
            self.aStart=90*16
            self.aSpan=90*16
        elif self.corner=="R":
            self.aStart=0
            self.aSpan=90*16
        else:
            assert False

    def boundingRect(self):
        if self.corner=="L":
            return QRectF(self.x-self.r,self.y-self.r,self.r,self.r)
        elif self.corner=="R":
            return QRectF(self.x,self.y-self.r,self.r,self.r)

    def paint(self,painter,option,widget=None):
        painter.drawArc(self.x-self.r,self.y-self.r,2*self.r,2*self.r,self.aStart,self.aSpan)


# class DTreeItem (QGraphicsItem):
#     """A graphics item representing a single dependency tree in its entirety"""
    
#     def __init__(self,modelS,x,y,hSpacing,vSpacing,parent=None,scene=None):
#         QGraphicsItem.__init__(self,parent,scene)
#         self.tree=modelS
#         """Holds a reference to its data model: a single Sentence instance"""
#         self.depItems={} #key: (gov,dep,type) value: depItem
#         self.tokenItems=[] #list of token items for easy access
#         self.build(x,y,hSpacing,vSpacing)

#     def build(self,x,y,hSpacing,vSpacing):
#         self.tokenContactXs,self.YBase=self.addTokens(hSpacing)
#         self.addDeps(self.tokenContactXs,self.YBase,vSpacing)
#         self.setPos(x,y)


        

class DTreeGraphicsScene (QGraphicsScene):

    def __init__(self,parent):
        QGraphicsScene.__init__(self,parent)
        self.tokenContactXs=None 
        """A list of x-coordinates of the tokens (mid-points)"""
        self.YBase=None
        """The Y coordinate where the dependencies start"""
        
    def layoutTree(self,tree,hSpacing,vSpacing):
        for c in self.items():
            self.removeItem(c)
        q=DTreeItem(tree,0,0,hSpacing,vSpacing,None,self)

    def editDepChange(self,oldG,oldD,oldT,newG,newD,newT,depItem):
        """Called by a dependency item that just got edited. Emits the requested signals to the"""
        pass

if __name__=="__main__":
    app = QApplication(sys.argv)
    tset=TreeSet.fromDXML(ET.parse("w001-viljanen.d.xml"))
    dtwidget=DTreeWidget()
    dtwidget.setModel(tset[0])
    dtwidget.buildGui()
    dtwidget.modelChanged()
    dtwidget.populateScene()
    dtwidget.show()
    sys.exit(app.exec_())
