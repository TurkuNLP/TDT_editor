#This is the LINUX Makefile
#for Windows, refer to compile.bat

#It seems pcre installs the includes into `pcre-config --prefix`/include
#If you get "cannot find pcre.h", find it ("locate pcre.h"),
#and put that directory as -I<dirname> on the following line
ALLINCLUDES=$(shell python-config --includes) -I$(shell pcre-config --prefix)/include

#Libs (plld takes care of all SWI Prolog -related headers and libs, here we need to
#take care of Python and PCRE)
ALLLIBS=$(shell python-config --libs) $(shell pcre-config --libs)

#...I don't think you should need to edit anything below this line, but... ;)

#What to build
TARGETS=treeseteditor_ui.py resfile_rc.py treesearchform_ui.py helpform_ui.py aboutform_ui.py

ALL: $(TARGETS)

#Compiles swiiface.so, using plld, the SWI prolog's compiler wrapper
swiiface.so: swiiface.c search_common.pl
	plld -embed-shared -class kernel -o $@ $(ALLINCLUDES) $(ALLLIBS) $<


#Builds python modules from the .ui files using pyuic4 from the pyqt4-dev-tools package
%_ui.py: %.ui
	pyuic4 -o $@ $<

#Builds python modules from the .qrc resource files using pyrcc4 from the pyqt4-dev-tools package
%_rc.py: %.qrc
	pyrcc4 -o $@ $<

clean:
	rm -f $(TARGETS) *~ *.pyc

