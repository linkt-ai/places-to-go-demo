FROM python:3.11

WORKDIR /app  

COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY rest ./rest
COPY checkpoints/bert-social.model ./checkpoints/

EXPOSE 8000 

CMD ["uvicorn", "rest.app:app", "--host", "0.0.0.0", "--port", "8000"]