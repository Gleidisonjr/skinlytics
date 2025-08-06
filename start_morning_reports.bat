@echo off
echo Iniciando Relatorios Matinais Skinlytics...
cd /d "C:\Users\dopamine\Desktop\Projetos\Projeto CSGO"
call .venv\Scripts\activate
python daily_morning_report.py --schedule
pause