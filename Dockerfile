FROM python:latest

WORKDIR /server

RUN apt-get update && apt-get upgrade 

COPY requirements.txt /server

RUN pip install -r /server/requirements.txt


EXPOSE 8000

ENTRYPOINT ["python", "-u", "server.py" ]
