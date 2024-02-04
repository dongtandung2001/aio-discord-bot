FROM nikolaik/python-nodejs:latest

WORKDIR /server

RUN apt-get update && apt-get upgrade 

COPY requirements.txt /server

RUN pip install -r /server/requirements.txt

RUN npm install -g nodemon

EXPOSE 8000

ENTRYPOINT ["nodemon", "server.py" , "--legacy-watch"]
