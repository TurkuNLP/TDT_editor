#Code by Sampo Pyysalo

import sys
import re

# PTB escape strings and replacement strings.
PTB_unescapes = (("-LRB-","("),
                 ("-RRB-",")"),
                 ("-LSB-","["),
                 ("-RSB-","]"),
                 ("-LCB-","{"),
                 ("-RCB-","}"))

def readStanfordDependencySentences(fileName):
    """Reads in dependencies from a file in the Stanford Dependendency format.
    returns a list of sentences, each a list of dependencies stored as 
    (deptype, headtxt, headidx, deptxt, depidx) tuples."""
    file = open(fileName)

    sentences = [[]]
    for l in file:
        if l == "" or l.isspace():
            # empty line separates sentences
            sentences.append([])
            continue

        # Note: allowing but ignoring the special syntax that SD
        # uses in some coordinated cases, identified with placing
        # a prime/single quote ("'") after the index.            
        m = re.match(r"^(.*?)\((.*)-(\d+)\'?, (.*)-(\d+)\'?\)$", l)
        assert m, "Error: failed to parse Stanford dependency '%s' in %s" % (l, fn)
        deptype, headtxt, headidx, deptxt, depidx = m.groups()
        headidx, depidx = int(headidx), int(depidx)
            
        # unescape PTB escapes in token text
        for e,u in PTB_unescapes:
            headtxt = headtxt.replace(e,u)
            deptxt  = deptxt.replace(e,u)

        sentences[-1].append((deptype, headtxt, headidx, deptxt, depidx))

    # newline after last sentence produces extra empty; remove
    if sentences[-1] == []:
        del sentences[-1]
        
    file.close()
    return sentences

def tokensFromDependencies(dependencies, fileName="<unknown file>"):
    """Given a list of dependencies represented as (deptype, headtxt,
    headidx, deptxt, depidx) tuples, returns a corresponding list of
    tokens."""

    tokentext = {}
    for deptype, headtxt, headidx, deptxt, depidx in dependencies:
        for txt, idx in ((headtxt, headidx), (deptxt, depidx)):
            if idx in tokentext and tokentext[idx] != txt:
                # TODO: warnings/errors somewhere else but stderr
                print >> sys.stderr, "Warning: disagreement for text of token %d in %s: '%s' vs '%s'" % (idx, fileName, txt, tokentext[idx])
            tokentext[idx] = txt

    # not all indices are necessarily filled; add defaults.
    for i in range(min(tokentext.keys()), max(tokentext.keys())):
        if i not in tokentext:
            tokentext[i] = "[...]"

    tlist = []
    for i in sorted(tokentext.keys()):
        tlist.append(tokentext[i])

    return tlist
