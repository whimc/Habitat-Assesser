# WHIMC-Habitat-Assesser Client

**This can currently only be ran on Windows machines!**

The client will run `habitat_assessment.py`. This script is responsible for sending information to the API whenever the server requests.
It connects to the server running `WHIMC-Habitat-Assesser` via a WebSocket to communicate.
The server will req

## Setup

```powershell
python -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
```

## Configure
```
python habitat_assessment.py 
```
