@echo off

if not exist "logs" mkdir logs
 
D:/Pedro/Data/.venv/Scripts/python.exe d:/Pedro/Data/run_multi_threshold.py -f 2000 -c 1 6 16 -b >> logs/2000.log 2>&1

D:/Pedro/Data/.venv/Scripts/python.exe d:/Pedro/Data/run_multi_threshold.py -f 5000 -c 1 6 16 -b >> logs/5000.log 2>&1

D:/Pedro/Data/.venv/Scripts/python.exe d:/Pedro/Data/run_multi_threshold.py -f 10000 -c 1 6 16 -b >> logs/10000.log 2>&1
