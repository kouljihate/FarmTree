@echo off
REM Create Farm Tree Manager project structure

set BASE=D:\Projects\Copilot\Farming\Tree\FarmTreeManager

REM Main folders
mkdir "%BASE%"
mkdir "%BASE%\BackEnd"
mkdir "%BASE%\FrontEnd"
mkdir "%BASE%\Share"
mkdir "%BASE%\tests"

REM BackEnd subfolders
mkdir "%BASE%\BackEnd\api"
mkdir "%BASE%\BackEnd\models"
mkdir "%BASE%\BackEnd\services"
mkdir "%BASE%\BackEnd\utils"

REM FrontEnd subfolders
mkdir "%BASE%\FrontEnd\ui"
mkdir "%BASE%\FrontEnd\assets"
mkdir "%BASE%\FrontEnd\components"

REM Share subfolders
mkdir "%BASE%\Share\config"
mkdir "%BASE%\Share\libs"
mkdir "%BASE%\Share\docs"

REM Create placeholder files
echo import flet as ft > "%BASE%\main.py"
echo flet==0.22.0 > "%BASE%\requirements.txt"
echo # Farm Tree Manager Project > "%BASE%\README.md"

echo Project structure created successfully!
pause
