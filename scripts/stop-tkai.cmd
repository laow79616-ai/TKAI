@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-tkai.ps1" %*
