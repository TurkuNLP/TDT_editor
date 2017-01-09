#This is the LINUX Makefile
#for Windows, refer to compile.bat

#It seems pcre installs the includes into `pcre-config --prefix`/include
#If you get "cannot find pcre.h", find it ("locate pcre.h"),
#and put that directory as -I<dirname> on the following line
ALLINCLUDES=$(shell python-config --includes) -I$(shell pcre-config --prefix)/include

#Libs (plld takes care of all SWI Prolog -related headers and libs, here we need to
#take care of Python and PCRE)
ALLLIBS=$(shell python-config --libs) $(shell pcre-config --libs)

PLLD=swipl-ld

#...I don't think you should need to edit anything below this line, but... ;)

#What to build
TARGETS=swiiface.so

ALL: $(TARGETS)

#Compiles swiiface.so, using plld, the SWI prolog's compiler wrapper
swiiface.so: swiiface.c search_common.pl
	$(PLLD) -embed-shared -class kernel -o $@ $(ALLINCLUDES) $(ALLLIBS) $<


clean:
	rm -f $(TARGETS)
