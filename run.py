import uvicorn
from config import PORT, BIND, WORKERS, RELOAD, DEBUG
import main

if __name__ == "__main__":
    uvicorn.run("main:app", host=BIND, port=int(PORT), reload=RELOAD, debug=DEBUG, workers=int(WORKERS))

#Run these commands from powershell with admin permissions.
#Remember to put service credentials in the right location C:/Users/samund/source/service_account_creds_manageschoolnotes.json

###############################################How to run this project########################################################
#cd C:/Users/samund/source/manageschoolnotes                    #change to the directory where the project is located
#pip install -r requirements.txt                                #install the required packages
#gcloud auth login                                              #login to your google cloud account
#gcloud config set project manageschoolnotes                    #set the project to the one you want to deploy to
#docker build -t gcr.io/manageschoolnotes/cloud-functions .     #build the docker image
#docker push gcr.io/manageschoolnotes/cloud-functions:latest    #push the docker image to the google cloud registry

# At this stage, the image is now in the google cloud registry. Now we can deploy the cloud function.
# The cloud function is deployed to the google cloud platform. It is a serverless function that is triggered by an HTTP request.
# Make sure you add all the environment variables in the cloud function.
# The environment variables are in the .env file.
#gcloud functions deploy manageschoolnotes --runtime python39 --trigger-http --allow-unauthenticated --memory=512MB --region=us-central1 --entry-point=app --source=cloud-functions
