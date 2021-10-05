# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /micro_wave

COPY . . 

RUN pip3 install .

COPY . . 
ENV PYTHONPATH=/micro_wave

ENTRYPOINT ["python", "micwave/src/main.py"]

