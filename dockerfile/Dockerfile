ARG BASE_PRIVATE_REGISTRY=""
FROM ${BASE_PRIVATE_REGISTRY}hkube/python-algorithm-base:v1.0.0
LABEL maintainer="yehiyam@gmail.com"
RUN mkdir /hkube
ADD . /hkube

WORKDIR /hkube
CMD ["python3","-u", "main.py"]