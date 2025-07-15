FROM python:3.11-slim

WORKDIR /app

COPY main.py main.py
COPY requirements.txt requirements.txt
COPY uploads/ uploads/   

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
