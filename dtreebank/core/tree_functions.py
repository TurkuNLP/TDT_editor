"""
dtreebank/core/tree_functions.py

Collection of functions to operate on the Tree class.

"""

import re

def find_circularity(tree,exclude=[],include="."):
    """Finds circular graphs in a given tree
    This is similar to the DFS-search by Filip in the Tree class,
    but with slight modifications to actually detect and
    report which tokens produce circular graphs.

    exclude=list of types not to be checked
    include=regular expression stating what dependency types are allowed.
   
    Error type: severe (no automic fixing, error in annotation)
    """
    tokens = [None for x in tree.tokens]
    deps={}
    r=re.compile(include)
    for (g,d,t) in tree.deps:
        if not r.match(t):
            continue
        if t not in exclude:
            deps.setdefault(g,set()).add(d)
    circles=[]
    for idx in range(len(tree.tokens)):
        if tokens[idx]!=None:
            continue
        if idx in deps: #this token is a governor (has dependencies)
            f_c_dfs(idx,[],deps,tokens,circles)
    return circles


def f_c_dfs(idx,indexes,deps,tokens,circles):
    """recursive support function for find_circularity"""
    tokens[idx]=True
    if idx in indexes:
        #Bingo, we have been here before, return all indexes
        #that are part of the circularity
        circles.append(indexes[indexes.index(idx):])
        return
    indexes.append(idx)
    if idx in deps:
        for i in deps[idx]:
            f_c_dfs(i,indexes[:],deps,tokens,circles)
          

def find_islands(tree,include="."):
    """Calculates the number of islands in a tree
    Error type: fixable (allows for automatic fixing)
    """
    roots={}
    deps=[]
    include_re=re.compile(include)
    for idx in range(len(tree.tokens)):
        roots[idx]=set([idx]) #root is also in the island
    for (gov,dep,type) in tree.deps: #index by (gov,dep,type)
        if not include_re.match(type):
            continue
        #Is this a new root or does it go inside another?
        if gov not in deps:
            #this governor has not yet been a dependency,
            #so we consider it a root
            roots[gov].add(dep)
            root=gov
        else:
            #this governor has already been a dependency,
            #so we add gov&dep into the same island
            for r in roots:
                if gov in roots[r]:
                    roots[r].add(gov)
                    roots[r].add(dep)
                    root=r
                    break
        deps.append(dep)
        #this only happens if there is circularity in a sentence,
        #but this function is not meant to die on those, so we
        #gracefully skip
        if root==dep:
            continue
        #if dep was considered before a root we move it under its governor
        if dep in roots:
            roots[root] = roots[root] | roots[dep]
            del roots[dep]
    return roots


def link_dependencies(tree,linkdeps):
    """Link given dependencies that are bridged over multiple
    tokens by creating a chainlink from governor to the dependant.

    To maintain tree structure we also remove all dependencies 
    under the bridge and move any deps coming from outside the bridge 
    to be connected to the governor

    returns: deps_removed, deps_relinked
    """

    deps_removed=[]
    deps_relinked=[]

    #we support multiple dependecy types at the same time
    if not isinstance(linkdeps,list):
        linkdeps=[linkdeps]
    bridgedeps=[]
    for (g,d,t) in tree.deps:
        if t in linkdeps:
            bridgedeps.append((g,d,t))

    bridgedeps.sort(key=lambda x:max(x[0],x[1])-min(x[0],x[1]), reverse=True)

    #clean stuff under bridged dependencies
    #and hang anything leaving or entering the bridge to the bridge gov.
    for (g,d,t) in tree.deps.copy():
        if (g,d,t) in bridgedeps:
            continue # we dont stuff other bridge dependencies
        for (bg,bd,bt) in bridgedeps:
            if (g,d,t)==(bg,bd,bt):
                continue
            if max(g,d)<=max(bg,bd) and min(g,d)>=min(bg,bd):
                #dependency inside bridge
                tree.editDepChange([(g,d,t,None,None,None)])
                deps_removed.append((g,d,t))
                break

            if bg>bd:
                # bridging from right to left
                if d<bg and d>=bd: #dependent inside bridge
                    tree.editDepChange([(g,d,t,g,bg,t)])
                    deps_relinked.append((g,d,t))
                    break
                if g<bg and g>=bd: #governor inside bridge
                    tree.editDepChange([(g,d,t,bg,d,t)])
                    deps_relinked.append((g,d,t))
                    break
            else:
                #bridging from left to right
                if d>bg and d<=bd: #dependent inside bridge
                    tree.editDepChange([(g,d,t,g,bg,t)])
                    deps_relinked.append((g,d,t))
                    break
                if g>bg and g<=bd: #governor inside bridge
                    tree.editDepChange([(g,d,t,bg,d,t)])
                    deps_relinked.append((g,d,t))


    # chain link the bridge
    for (g,d,t) in bridgedeps:
        assert (g,d,t) in tree.deps
        if max(g,d)-min(g,d)>1:
            if g>d:
                chgs=[(None,None,None,x+1,x,t) for x in range(d,g)]
            else:
                chgs=[(None,None,None,x,x+1,t) for x in range(g,d)]
            chgs.append((g,d,t,None,None,None))
            tree.editDepChange(chgs)
            deps_removed.append((g,d,t))

    return deps_removed, deps_relinked

