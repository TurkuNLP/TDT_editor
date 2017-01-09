.PHONY=guimodules swisearchmodules common

all: guimodules 

CG:
	make -C dtreebank/CG

guimodules:
	make -C dtreebank/gui

clean:
	make -C dtreebank/gui clean
	make -C dtreebank/CG clean

# this is for maintenance purposes..
# to pull updates from cvs if needed.
cvsupdate:
	rm -f dtreebank/cElementTreeUtils.py
	cvs export -d dtreebank -fD now CommonUtils/cElementTreeUtils.py
	rm -f dtreebank/draw_dg.py
	cvs export -d dtreebank -fD now CommonUtils/draw_dg.py
	rm -f dtreebank/iterableutils.py
	cvs export -d dtreebank -fD now CommonUtils/iterableutils.py
