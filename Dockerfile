FROM python:3.11-slim

WORKDIR /app

COPY server.py .
COPY index.html .

RUN pip install psutil

EXPOSE 7000

CMD ["python", "server.py"]