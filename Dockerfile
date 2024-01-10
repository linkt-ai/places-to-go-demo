FROM python:3.11

WORKDIR /app  

COPY src/flask/ ./flask_app/
COPY models/bert-social.model ./models/

RUN pip install --upgrade pip
RUN pip install torch transformers flask

EXPOSE 8080 

ENTRYPOINT ["python", "-m"]
CMD ["flask_app"]