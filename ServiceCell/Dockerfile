FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get -y install vim iproute2 curl tmux 
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
COPY .tmux.conf /
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install gunicorn

EXPOSE 8080
EXPOSE 51313

COPY CellController-mp.py Loader.py ExternalServiceExecutor.py InternalServiceExecutor.py mub.proto mub_pb2.py \
    mub_pb2_grpc.py gunicorn.conf.py start-mp.sh ./

CMD [ "/bin/bash", "/app/start-mp.sh"]

