FROM python:3.7.4-alpine3.10
RUN pip install \
  black==19.3b0 \
  flake8==3.7.8
WORKDIR /python
