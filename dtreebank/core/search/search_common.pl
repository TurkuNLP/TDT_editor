%%% Predicates for the tree search
%%%
%%% To search, the Python GUI builds and asserts a tokenQuery/3 predicate
%%% which unifies the TokenSetID,SentenceID,TokenSequence variables for
%%% individual matching tokens. This tokenQuery/3 predicate is built from
%%% the search expression the user gives (in swisearch.py)
%%%
%%% dosearch/1 simply builds a set of all matches...
%%%
%%% the regular expression functionality is in swiiface.c (calls PCRE)
%%%


%%sentenceQuery/2 currently unused

:-dynamic sentenceQuery/2,tokenQuery/3,dep/5,token/4,cgreading/5,twolreading/5,arg/5,flag/5,frame/4.
:-multifile tokenQuery/3,dep/5,token/4,cgreading/5,twolreading/5,arg/5,flag/5,frame/4.
:-consult('lists').
:-index(token(1,1,1,1)).
:-index(cgreading(1,1,1,1,0)).
:-index(twolreading(1,1,1,1,0)).
:-index(dep(1,1,1,1,0)).
:-index(arg(1,1,1,1,0)).
:-index(flag(1,1,1,1,0)).
:-index(frame(1,1,1,1)).

hasCGTag(TSetID,SentID,TokenSeq,Tag):-
	cgreading(TSetID,SentID,TokenSeq,_,AllTags),
	member(Tag,AllTags).

hasTWTag(TSetID,SentID,TokenSeq,Tag):-
	twolreading(TSetID,SentID,TokenSeq,_,AllTags),
	member(Tag,AllTags).


hasCGBaseForm(TSetID,SentID,TokenSeq,Base):-
	cgreading(TSetID,SentID,TokenSeq,Base,_).

hasTWBaseForm(TSetID,SentID,TokenSeq,Base):-
	twolreading(TSetID,SentID,TokenSeq,Base,_).

dosearch(Set) :-
	findall([TSetID,SentID,TokenSeq],tokenQuery(TSetID,SentID,TokenSeq),Bag),
	list_to_set(Bag,Set).


cleanup :- retractall(tokenQuery(_,_,_)),retractall(sentenceQuery(_,_)).

cleanupdata :- retractall(token(_,_,_,_)),retractall(dep(_,_,_,_,_)),retractall(cgreading(_,_,_,_,_)),retractall(twolreading(_,_,_,_,_)),retractall(arg(_,_,_,_,_)),retractall(frame(_,_,_,_)),retractall(flag(_,_,_,_,_)).

unloadtreeset(ID):-retractall(token(ID,_,_,_)),retractall(dep(ID,_,_,_,_)),retractall(cgreading(ID,_,_,_,_)),retractall(twolreading(ID,_,_,_,_)),retractall(arg(ID,_,_,_,_)),retractall(frame(ID,_,_,_)),retractall(flag(ID,_,_,_,_)).
