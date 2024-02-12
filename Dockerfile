FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY . .

COPY service_account_creds_manageschoolnotes.json /app
#COPY C:/Users/samund/source/service_account_creds_manageschoolnotes.json /app
RUN pip install firebase-admin firebase-admin typing pydantic unidecode pytz

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
#uvicorn.run("main:application", host=BIND, port=int(PORT), reload=RELOAD, debug=DEBUG, workers=int(WORKERS))
