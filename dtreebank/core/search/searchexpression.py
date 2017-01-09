import re

import dtreebank.core.search.lex as lex
import dtreebank.core.search.yacc as yacc

class ExpressionError(ValueError):

    pass

class TreeRoot(object):

    def __init__(self):
        self.rootProperties={} #token restrictions
        self.depRestrictions=[] #dependency restrictions
        self.prologVar=None

    def numberTokens(self,counter): #unique token numbering for prolog variables
        self.prologVar=u"T"+unicode(counter)
        counter+=1
        for dr in self.depRestrictions:
            if dr.dep!=None:
                counter=dr.dep.numberTokens(counter)
            elif dr.gov!=None:
                counter=dr.gov.numberTokens(counter)
        return counter #...next available token number

    def addDepRestriction(self,dr):
        self.depRestrictions.append(dr)

    def addRestriction(self,(label,value)):
        self.rootProperties[label]=value
        

    def tokenPrologRealization(self,positive,settings):
        predicates=[]
        #print self.rootProperties



        #TEXT, direct
        if positive and u"TXT" in self.rootProperties:
            txtPs=set()
            for txt in self.rootProperties[u"TXT"].split(u"|"):
                txtPs.add(u"token(TSetID,SentID,%s,'%s')"%(self.prologVar,txt))
                if not settings.get(u"case-sensitive"):
                    txtPs.add(u"token(TSetID,SentID,%s,'%s')"%(self.prologVar,txt.capitalize()))
                    txtPs.add(u"token(TSetID,SentID,%s,'%s')"%(self.prologVar,txt.upper()))
                    txtPs.add(u"token(TSetID,SentID,%s,'%s')"%(self.prologVar,txt.lower()))
            if len(txtPs)==1:
                predicates.append(txtPs.pop())
            else:
                predicates.append(u"("+u" ; ".join(txtPs)+u")")

        #CGBASE
        if positive and u"CGBASE" in self.rootProperties:
            bases=[u"cgreading(TSetID,SentID,%s,'%s',_)"%(self.prologVar,oneBase) for oneBase in self.rootProperties[u"CGBASE"].split(u"|")]
            if len(bases) == 1:
                predicates.extend(bases)
            else:
                predicates.append(u"("+u" ; ".join(bases)+u")")
        #CGBASE
        if positive and u"CGTAG" in self.rootProperties:
            for tag in self.rootProperties[u"CGTAG"].split(u"+"):
                predicates.append(u"hasCGTag(TSetID,SentID,%s,'%s')"%(self.prologVar,tag))
        #TWBASE
        if positive and u"TWBASE" in self.rootProperties:
            bases=[u"twolreading(TSetID,SentID,%s,'%s',_)"%(self.prologVar,oneBase) for oneBase in self.rootProperties[u"TWBASE"].split(u"|")]
            if len(bases) == 1:
                predicates.extend(bases)
            else:
                predicates.append(u"("+u" ; ".join(bases)+u")")
        #TWBASE
        if positive and u"TWTAG" in self.rootProperties:
            for tag in self.rootProperties[u"TWTAG"].split(u"+"):
                predicates.append(u"hasTWTag(TSetID,SentID,%s,'%s')"%(self.prologVar,tag))
        if u"FR" in self.rootProperties:
            if self.rootProperties[u"FR"]==u"none":
                if not positive:
                    predicates.append(u"\+ frame(TSetID,SentID,%s, _)"%(self.prologVar))
            elif positive:
                predicates.append(u"frame(TSetID,SentID,%s, '%s')"%(self.prologVar,self.rootProperties[u"FR"]))
        #TEXT, REGULAR EXPRESSION
        if settings.get(u"case-sensitive"):
            matchP=u"accepts"
        else:
            matchP=u"accepts_caseless"
        if positive and u"TXTRE" in self.rootProperties:#A regular expression is given constraining the text
            predicates.append(u"token(TSetID,SentID,%s,%sTXT)"%(self.prologVar,self.prologVar))
            predicates.append(u"%s('%s',%sTXT)"%(matchP,self.rootProperties[u"TXTRE"],self.prologVar))
        return u", ".join(predicates)

    def dummyPrologRealization(self,settings):
        #Provides a dummy token if necessary (in case of negative-only dependency restrictions)
        return u"token(TSetID,SentID,%s,_)"%self.prologVar

    def prologRealization(self,settings):
        predicates=[]
        tokenPL=self.tokenPrologRealization(True,settings) #Positive Restriction on the token itself. Gives empty string for trivial "_"
        if tokenPL:
            predicates.append(tokenPL)
        #Now go through all positive dependency restrictions, if any
        posDRs=[dr for dr in self.depRestrictions if not dr.negated]
        negDRs=[dr for dr in self.depRestrictions if dr.negated]
        nonUnifyList=[]
        for dr in posDRs:
            predicates.append(dr.prologRealization(self.prologVar,nonUnifyList,settings))
            nonUnifyList.append(dr.restrictionTokenVar())
        tokenNegPL=self.tokenPrologRealization(False,settings)
        if not predicates and (len(negDRs)>0 or tokenNegPL): #no positive, but some negative restrictions -> need a placeholder definition
            predicates.append(self.dummyPrologRealization(settings))
        if tokenNegPL:
            predicates.append(tokenNegPL)
        for dr in negDRs:
            predicates.append(dr.prologRealization(self.prologVar,[],settings)) #no non-unify restrictions for negative
        return u", ".join(predicates)
    
            
        

class DepRes(object):

    def __init__(self,depop,expr):
        self.dep=None # Either one of these will be set to TreeRoot
        self.gov=None # the other remains none and is implied to be the TreeRoot under which this DepRes belongs
        self.properties={} #dependency type and argument restrictions
        self.negated=False

        match=re.match(t_DEPOP,depop,re.U)
        assert match
        self.operator=match.group(1)
        if self.operator==u"<":
            #Governor specified by expr
            self.gov=expr
        elif self.operator==u">":
            self.dep=expr
        else:
            assert False
        spec=match.group(2)
        if spec!=None:
            spec=spec[1:-1] #strip the /../
            parts=spec.split(u"&")
            for part in parts:
                if part.startswith(u"A="):
                    #restricts argument
                    self.properties[u"ARGLIST"]=part[2:].split(u"|")
                elif part.startswith(u"F="):
                    #restricts flag
                    self.properties[u"FLAGLIST"]=part[2:].split(u"|")
                else: #dep types
                    if part.startswith(u"DT="):
                        part=part[3:]
                    self.properties[u"DTYPELIST"]=part.split(u"|")
                    
    def restrictionTokenVar(self):
        if self.dep!=None:
            return self.dep.prologVar
        elif self.gov!=None:
            return self.gov.prologVar
        else:
            assert False
                           

    def prologRealization(self,rootPrologVar,nonUnifyList,settings):
        #nonUnifyList is a list of variables own restriction variable should not unify with
        #this is to avoid repeated restrictions hitting the same token (like asking for two nommod dependencies returning twice the same token)
        if self.dep!=None: #This one restricts on a dependent
            depVar=self.dep.prologVar
            govVar=rootPrologVar
        elif self.gov!=None:
            depVar=rootPrologVar
            govVar=self.gov.prologVar
        else:
            assert False
            
        
        predicates=[]

        if u"ARGLIST" in self.properties:
            args=[u"ARG"+a for a in self.properties[u"ARGLIST"]]
            if len(args)==1:
                predicates.append(u"arg(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,args[0]))
            else:
                predicates.append(u"("+u" ; ".join(u"arg(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,a) for a in args)+u")")
        if u"FLAGLIST" in self.properties:
            flags=self.properties[u"FLAGLIST"]
            if len(flags)==1:
                predicates.append(u"flag(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,flags[0]))
            else:
                predicates.append(u"("+u" ; ".join(u"arg(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,f) for f in flags)+u")")
        if u"DTYPELIST" in self.properties:
            dTypes=self.properties[u"DTYPELIST"]
            if len(dTypes)==1:
                predicates.append(u"dep(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,dTypes[0]))
            else:
                predicates.append(u"("+u" ; ".join(u"dep(TSetID,SentID,%s,%s,'%s')"%(govVar,depVar,dType) for dType in dTypes)+u")")

        if not predicates: #No non-trivial restrictions - must make a dummy dep
            predicates.append(u"dep(TSetID,SentID,%s,%s,_)"%(govVar,depVar))

        if self.dep!=None:
            childPrologRealization=self.dep.prologRealization(settings)
        elif self.gov!=None:
            childPrologRealization=self.gov.prologRealization(settings)
        else:
            assert False

        if childPrologRealization:
            predicates.append(childPrologRealization)
        
        childVar=self.restrictionTokenVar()
        for var in nonUnifyList:
            predicates.append(ur"%s\=%s"%(var,childVar))
        
        result=u", ".join(predicates)
        if self.negated:
            result=ur"\+ ("+result+u")"
        return result
                                



#Lexer

tokens=('REGEX',
        'PROPLABEL',
        'DEPOP',
        'LPAR',
        'RPAR',
        'NEG',
        'ANYTOKEN')

t_REGEX=ur"/[^/]+/"
t_PROPLABEL=ur"@[A-Z]+"
t_DEPOP=ur"(<|>)(/[^/]+/)?"
t_LPAR=ur"\("
t_RPAR=ur"\)"
t_NEG=ur"!"
t_ANYTOKEN=ur"_"

t_ignore=u" \t"

def t_error(t):
    raise ExpressionError(u"Unexpected character '%s'\nHERE: '%s'..."%(t.value[0],t.value[:5]))


#Main 
precedence = ( ('left','DEPOP'), )

def p_error(t):
    if t==None:
        raise ExpressionError(u"Syntax error at the end of the expression. Perhaps you forgot to specify a target token? Forgot to close parentheses?")
    else:
        raise ExpressionError(u"Syntax error at the token '%s'\nHERE: '%s'..."%(t.value,t.lexer.lexdata[t.lexpos:t.lexpos+5]))

def p_top(t):
    u'''search : expr'''
    t[0]=t[1]

def p_expr2(t):
    u'''expr : expr depres
             | expr NEG depres'''
    t[0]=t[1]
    if len(t)==3:
        t[0].addDepRestriction(t[2]) #not negated
    elif len(t)==4:
        t[3].negated=True
        t[0].addDepRestriction(t[3]) #negated

def p_depres(t):
    u'''depres : DEPOP expr'''
    t[0]=DepRes(t[1],t[2])

def p_exprp(t):
    u'''expr : LPAR expr RPAR
              | ANYTOKEN'''
    if len(t)==4:
        t[0]=t[2]
    elif len(t)==2:
        t[0]=TreeRoot()

def p_exprp2(t):
    u'''expr : tokendef'''
    t[0]=t[1]

def p_tokendef(t):
    u'''tokendef : prop
                 | prop tokendef'''
    if len(t)==2:
        t[0]=TreeRoot()
        t[0].addRestriction(t[1])
    elif len(t)==3:
        t[0]=t[2]
        t[0].addRestriction(t[1])

def p_prop(t):
    u'''prop : REGEX
             | PROPLABEL REGEX'''
    if len(t)==2:
        t[0]=(u"TXT",unicode(t[1][1:-1])) #strip the /../
    elif len(t)==3:
        t[0]=(unicode(t[1][1:]),unicode(t[2][1:-1])) #strip the /../


def prologRealization(expr,caseSensitive):
    root=yacc.parse(expr) #throws an ExpressionError if parsing the expression doesn't work out
    root.numberTokens(0)
    exprPL=root.prologRealization({u"case-sensitive":caseSensitive})
    headT=root.prologVar
    return headT,exprPL

def assertStatement(expr,caseSensitive=False):
    headT,exprPL=prologRealization(expr,caseSensitive)
    return u"assert( ( tokenQuery(TSetID,SentID,%s) :- ( %s ) ) )."%(headT,exprPL)

lex.lex(reflags=re.UNICODE)
yacc.yacc(write_tables=0)

