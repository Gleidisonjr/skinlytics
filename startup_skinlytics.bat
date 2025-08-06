
@echo off
cd /d "C:\Users\dopamine\Desktop\Projetos\Projeto CSGO"
call .venv\Scripts\activate
python scale_collection.py --interval 600
pause
        