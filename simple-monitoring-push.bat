@echo off
cd c:\Users\renderkar\Documents\NOCbRAIN

echo Adding monitoring agent files...
git add agents/
git add backend/app/modules/monitoring/
git add backend/app/api/endpoints/monitoring.py
git add backend/app/schemas/monitoring.py

echo Committing monitoring agent update...
git commit -m "Add secure monitoring agent system"

echo Pushing to GitHub...
git push origin main

echo Done!
pause
