FROM continuumio/miniconda3

WORKDIR /usr/src/mars

SHELL ["/bin/bash", "--login", "-c"]

RUN conda create -n mars python=3.9
RUN conda init bash

RUN conda activate mars
RUN conda install -c conda-forge dlib

RUN pip install --upgrade pip
RUN pip install face_recognition
COPY ./requirements.txt /usr/src/mars/
RUN pip install -r requirements.txt

ENV FLASK_APP=source/__init__.py

COPY . /usr/src/mars/