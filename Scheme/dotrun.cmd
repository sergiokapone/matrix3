@echo off
set YEAR=%~1
set NAME="diagramm_bak_%YEAR%"
dot -Tpdf %NAME%.gv -o %NAME%.pdf
