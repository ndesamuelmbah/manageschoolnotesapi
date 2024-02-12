import uvicorn
from config import PORT, BIND, WORKERS, RELOAD, DEBUG
import main

if __name__ == "__main__":
    uvicorn.run("main:app", host=BIND, port=int(PORT), reload=RELOAD, debug=DEBUG, workers=int(WORKERS))

#Run these commands from powershell with admin permissions.
#Remember to put service credentials in the right location C:/Users/samund/source/service_account_creds_manageschoolnotes.json
#gcloud auth login
#gcloud config set project manageschoolnotes
#docker build -t gcr.io/manageschoolnotes/cloud-functions .
#docker push gcr.io/manageschoolnotes/cloud-functions:latest
