# StaffWork
## Backend
`cd backend`
`pip install -r requirements.txt`
`python app.py`
!Make port public if you are using codespace

## Frontend
`cd frontend`
`npm install -g npm`
`npm i`
!update .env VITE_API_URL to point to public address of backend
`npm run dev`

## LLM Server
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 5001 OR
uvicorn chatgpt:app --reload --host 0.0.0.0 --port 5001