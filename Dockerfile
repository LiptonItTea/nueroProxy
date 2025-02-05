FROM python:latest

WORKDIR /project

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /project

ENTRYPOINT ["python", "main.py"]