Start-Process python.exe .\server.py
Start-Sleep -Milliseconds 100
Start-Process python.exe .\inspector.py
Start-Sleep -Milliseconds 100
Start-Process python.exe .\fantom.py -Wait