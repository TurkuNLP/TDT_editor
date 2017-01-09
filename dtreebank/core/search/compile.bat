call vcvarsall.bat
plld -v -dll -o swiiface.pyd -Ic:\swipl\pl\include -Ic:\Python26\include -Ic:\GnuWin32\include -Lc:\Python26\libs -Lc:\GnuWin32\lib swiiface.c c:\GnuWin32\lib\pcre.lib
