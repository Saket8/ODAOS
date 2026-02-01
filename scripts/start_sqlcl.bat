@echo off
REM Setup SQLcl MCP Server for ODAOS
REM This script configures SQLcl with saved database connections

SET JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.18.8-hotspot
SET SQLCL_HOME=C:\Users\2016tu\Downloads\sqlcl-latest\sqlcl

echo ================================================
echo ODAOS SQLcl MCP Server Setup
echo ================================================
echo.
echo IMPORTANT: SSH tunnel must be running before connecting!
echo Run this first in another terminal:
echo   python -c "from src.database.tunnel import SSHTunnelManager; t=SSHTunnelManager(); t.start(); input('Tunnel running. Press Enter to stop...')"
echo.
echo ================================================
echo.

REM Start SQLcl
"%SQLCL_HOME%\bin\sql.exe" /nolog

