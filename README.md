The program has been tested and works on an off-the-shelf Ubuntu
system, if you follow the instructions below (i.e. install PyQT4 and
PCRE directly from the system repositories)

RUNNING:

The program comes with a pre-compiled Prolog interface library
(swiiface.so) and pre-generated Qt4 UI modules. In theory, all you
should need is to make sure you have everything necessary installed
and run. In case something fails, you may need to recompile for your
system (see below).

1) Make sure you have recent versions of all the necessary
dependencies installed. In parentheses are given the package names in
Ubuntu (and derivatives, probably also Debian and derivatives...)
Install these with "sudo apt-get install <packagename>".

   * Python Qt4 bindings (python-qt4)

   * PCRE library (libpcre3)

2) run "python treeseteditor.py"


RECOMPILING:

If you get errors when trying to run the program (library
incompatibilities and the like), you might try to recompile:

1) Make sure you have the header files / development tools for the necessary dependencies installed:

   * SWI Prolog (swi-prolog)

   * Python Qt4 bindings (python-qt4-dev AND pyqt4-dev-tools)

   * PCRE library header files (libpcre3-dev)

2) make clean
   make swiiface.so

3) run "python treeseteditor.py"
