\# LogWatcher + ChatGPT (Python)
 
1) Setup

1.1) Open the project folder : cd path\to\logwatcher_ai
* Create a virtual environment (Optional):
```bash
python -m venv .venv

1.2) Install deps
Windows PowerShell:
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt

1.3) Set environment variables - OpenAI API key - TBD
Windows PowerShell or VS Code Terminal:
setx OPENAI_API_KEY "openai-api-key"

1.4) Set Log file path (optional, defaults to demo.log)
Windows PowerShell or VS Code Terminal:
setx LOG_PATH "demo.log"

1.3.1/1.4.1) Note: After running setx:
* Close all VS Code windows
* Reopen VS Code
* Reopen the project folder

-----------------------------------------------------------------------------------------------------------

2) Connect Log generator
Start the Docker container

2.1) List containers:
docker ps -a

2.2) Start the target container:
docker start <container_name>

2.3) Pipe Docker logs into demo.log
docker logs -f <container_name> 2>&1 | Tee-Object -FilePath demo.log -Append

-----------------------------------------------------------------------------------------------------------

3) Start the LogWatcher API

3.1) On a separate terminal reload the app
python -m uvicorn app:app --reload

3.2) verify system running

3.2.1) Health check
http://127.0.0.1:8000/health

3.2.2) Live logs dashboard
http://127.0.0.1:8000/logs

3.2.3) API docs
http://127.0.0.1:8000/docs

-----------------------------------------------------------------------------------------------------------


