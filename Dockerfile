# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /micro_wave

COPY . . 

# Install all requirements, with those for notebook included.
RUN pip3 install .[pres]

COPY . . 
ENV PYTHONPATH=/micro_wave

# ENTRYPOINT ["python", "micwave/src/main.py"]

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]
