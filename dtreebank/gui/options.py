#Global options currently in effect
from optparse import OptionParser

options=None
args=None

setup={"depsFile":"depTypes"}

#treePaneAlert -> color-coded background
#textEdit -> sentence splitting/merging, token editing
setupPB={"treePaneAlert":False,"textEdit":False}
setupTDT={"treePaneAlert":True,"textEdit":False}
setupSD={"depsFile":"depTypes.sd","treePaneAlert":False,"textEdit":False,"history_suffix":""}
setupUD={"depsFile":"depTypes","treePaneAlert":True,"textEdit":False,"history_suffix":"U"}
setupUDF={"depsFile":"depTypes","treePaneAlert":False,"textEdit":False,"history_suffix":"F"}

def parseOptions():
    global options,args,setup
    parser = OptionParser(description="treeset editor")
    parser.add_option("--nocgcache", dest="usecgcache",action="store_false", default=True, help="Ignore cached CG analyses from .d.xml files and rerun CG from scratch")
    parser.add_option("--config", dest="config",action="store", default="UD", help="Annotator config: SD or UD or UDF.")
    options, args = parser.parse_args()
    
    if options.config=="TDT":
        setup=setupTDT
    elif options.config=="PB":
        setup=setupPB
    elif options.config=="SD":
        setup=setupSD
    elif options.config=="UD":
        setup=setupUD
    elif options.config=="UDF":
        setup=setupUDF

    for k,v in options.__dict__.items():
        if v!=None:
            setup[k]=v

    #Other defaults
