FROM python:3.8.1-alpine
ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    jpeg-dev \
    postgresql-dev \
    tzdata

COPY /requirements.txt /requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r /requirements.txt
RUN mkdir /app
WORKDIR /app
COPY /drfsite /app
RUN adduser -D user
USER user