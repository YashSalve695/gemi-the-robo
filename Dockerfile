FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "$PORT"]