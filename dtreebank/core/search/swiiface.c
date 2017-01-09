#include <Python.h>
#include <SWI-Prolog.h>
#include <pcre.h>
#include <stdio.h>

//REGULAR EXPRESSION FOREIGN PREDICATES
//Lifted from their separate project to here to simplify compilation and linking a bit

foreign_t pl_accepts_flags(term_t patternTerm, term_t stringTerm, int extraFlags) {
    char *string,*pattern;
    pcre *regex;
    const char *error;
    int erroroffset;
    int ovector[30];
    int r;
    PL_get_chars(stringTerm, &string, CVT_ATOM|REP_UTF8);
    PL_get_chars(patternTerm, &pattern, CVT_ATOM|REP_UTF8);
    regex=pcre_compile(pattern, PCRE_ANCHORED|PCRE_UTF8|extraFlags, &error, &erroroffset, NULL);
    if (regex==NULL) {
        printf("Regex: Compilation failed\n");
        PL_fail;
    }
    r=pcre_exec(regex,NULL,string,strlen(string),0,0,ovector,30);
    pcre_free(regex);
    if (r>=0) {
        PL_succeed;
    }
    else {
        PL_fail;
    }
}

foreign_t pl_accepts(term_t patternTerm, term_t stringTerm) {
    return pl_accepts_flags(patternTerm, stringTerm, 0);
}


foreign_t pl_accepts_caseless(term_t patternTerm, term_t stringTerm) {
    return pl_accepts_flags(patternTerm, stringTerm, PCRE_CASELESS);
}

//PYTHON-PROLOG INTERFACE (also registers the regex predicates above)

static PyObject *swiiface_initPL(PyObject *self,PyObject *args) {
    int ok;
    int *dummyargc=NULL; //used in the _is_initialised call
    char ***dummyargv=NULL; //used in the _is_initialised call
    char *argv0;

    if ( PL_is_initialised(dummyargc, dummyargv) ) { //Do nothing if already initialized
	Py_RETURN_NONE;
    }

    ok=PyArg_ParseTuple(args, "s", &argv0);
    if (!ok) {
	fprintf(stderr,"argv[0] not passed to initPL()\n");
	return NULL;
    }
    else {
	puts(argv0);
    }
    if ( !PL_initialise(1, &argv0) ) {
	fprintf(stderr,"Failed prolog initialization\n");
	PL_halt(1);
	return NULL;
    }
    ok=PL_register_foreign_in_module(NULL,"accepts",2,pl_accepts,0);
    if (! ok) {
	fprintf(stderr,"Failed to register accepts/2\n");
	PL_halt(1);
	return NULL;
    }
    ok=PL_register_foreign_in_module(NULL,"accepts_caseless",2,pl_accepts_caseless,0);
    if (! ok) {
	fprintf(stderr,"Failed to register accepts_caselesss/2\n");
	PL_halt(1);
	return NULL;
    }
    Py_RETURN_NONE;
}

//From a list of three integer atoms, builds a python tuple
//The triple is one matching token (treesetID,sentenceID,tokenSeq)
static PyObject *buildTriple(term_t oneMatch) {
    term_t head = PL_new_term_ref();
    term_t list = PL_copy_term_ref(oneMatch);
    int tsetID;
    int sentID;
    int tokenSeq;
    PL_get_list(list,head,list);
    PL_get_integer(head,&tsetID);
    PL_get_list(list,head,list);
    PL_get_integer(head,&sentID);
    PL_get_list(list,head,list);
    PL_get_integer(head,&tokenSeq);
    return Py_BuildValue("(iii)",tsetID,sentID,tokenSeq);
}


//For a list of [treesetID,sentenceID,tokenSeq], builds
//a Python list of triples
static PyObject *buildResultList(term_t l) {
    term_t head = PL_new_term_ref();
    term_t list = PL_copy_term_ref(l);
    PyObject *oneTriple;
    PyObject *resList=PyList_New(0);

    while( PL_get_list(list, head, list) ) {
	oneTriple=buildTriple(head);
	PyList_Append(resList,oneTriple);
    }
    return resList;
  }


//Calls the "dosearch/1" predicate in search_common.pl and
//translates its result into a Python list of triples
static PyObject *swiiface_matchingSentences(PyObject *self,PyObject *args) {
    fid_t fid;
    term_t goal;
    int ok;

    term_t queryAnswer;
    qid_t query;
    predicate_t queryPredicate;

    PyObject *result;

    fid=PL_open_foreign_frame();
    queryAnswer=PL_new_term_refs(1);
    
    queryPredicate=PL_predicate("dosearch",1,NULL);
    query=PL_open_query(NULL,PL_Q_CATCH_EXCEPTION,queryPredicate,queryAnswer);
    if (PL_next_solution(query)) {
	result=buildResultList(queryAnswer);
	PyList_Sort(result);
	PL_close_query(query);
	PL_close_foreign_frame(fid);
	return result;
    }
    else {
	PL_close_query(query);
	PL_close_foreign_frame(fid);
	Py_RETURN_NONE;
    }
}


//Calls an arbitrary Prolog goal. Used from the Python call to assert
//tokenQuery, clean-up, etc. 
static PyObject *swiiface_callPL(PyObject *self,PyObject *args) {
    fid_t fid;
    term_t goal;
    char *goalString;
    int ok;

    ok=PyArg_ParseTuple(args, "s", &goalString);
    if (!ok) {
	fprintf(stderr,"execPL expects a string as its argument");
	return NULL;
    }

    //all is OK, will run the goal through prolog

    fid=PL_open_foreign_frame();
    goal=PL_new_term_ref();
    
    ok=PL_chars_to_term(goalString,goal);
    if (!ok) {
	fprintf(stderr,"error in the goal string:\n");
	fprintf(stderr,">>> %s\n",goalString);
	PL_close_foreign_frame(fid);
	Py_RETURN_NONE;
    }
    ok=PL_call(goal,NULL);
    PL_close_foreign_frame(fid);
    if (!ok) {
	Py_RETURN_FALSE;
    }
    else {
	Py_RETURN_TRUE;
    }
}

    
static PyMethodDef SwiifaceMethods[] = {
    {"initPL",  swiiface_initPL, METH_VARARGS,"Initialize Prolog."},
    {"callPL",  swiiface_callPL, METH_VARARGS,"Execute the given query."},
    {"matchingSentences",  swiiface_matchingSentences, METH_VARARGS,"Return a list of matching sentences."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
initswiiface(void)
{
    (void) Py_InitModule("swiiface", SwiifaceMethods);
}
