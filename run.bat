@echo off
chcp 65001 >nul
py main.py
if %errorlevel% neq 0 pause
