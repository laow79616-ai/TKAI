# Windows local guide

Use the existing PowerShell local-runtime scripts from an ordinary user shell.
The engine uses the same loopback API, logs, metrics, backups, and runtime
manager. No extra service, credential file, or public listener is required.
Run the Python checks from `.venv` and build both frontend workspaces with their
existing package scripts before committing.
