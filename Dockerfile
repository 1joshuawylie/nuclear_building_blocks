# syntax=docker/dockerfile:1

FROM python:3.9-slim-bullseye
SHELL ["/bin/bash", "-c"]

RUN mkdir wd
WORKDIR wd

COPY . .

ARG TARGETPLATFORM

COPY requirements.txt .
RUN pip3 install -r requirements.txt

CMD [ "gunicorn", "--worker-class=gevent", "--workers=9", "--threads=1", "-b 0.0.0.0:80", "app:server"]
