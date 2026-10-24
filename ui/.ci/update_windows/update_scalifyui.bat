@echo off
..\python_embeded\python.exe .\update.py ..\ScalifyUI\
if exist update_new.py (
  move /y update_new.py update.py
  echo Running updater again since it got updated.
  ..\python_embeded\python.exe .\update.py ..\ScalifyUI\ --skip_self_update
)
if "%~1"=="" pause
