FROM python:latest

WORKDIR /server

RUN apt-get update 

RUN apt-get -y install ffmpeg

RUN apt-get -y install tesseract-ocr

RUN apt-get -y install libtesseract-dev

COPY requirements.txt /server

RUN pip install -r /server/requirements.txt


EXPOSE 8000

ENTRYPOINT ["python", "-u", "server.py" ]
