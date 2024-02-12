# manageschoolnotesapi

#Run these commands from powershell with admin permissions.
#Remember to put service credentials in the right location C:/Users/samund/source/service_account_creds_manageschoolnotes.json

## Here are the commands for building and deploying.
# clone the project iand cd into root folder manageschoolnotesapi
#gcloud auth login
#gcloud config set project manageschoolnotes
#docker build -t gcr.io/manageschoolnotes/manageschoolnotesapi .
#docker push gcr.io/manageschoolnotes/manageschoolnotesapi:latest

## You can also use a single command like so.
#docker build -t gcr.io/manageschoolnotes/manageschoolnotesapi . && docker push gcr.io/manageschoolnotes/manageschoolnotesapi:latest

#Alternatively, to follow a step by step approach
# gcloud run deploy
# gcloud app deploy