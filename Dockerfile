FROM python:3.10

ARG BITBUCKET_TAG
ADD ./dist/dtlpy-$BITBUCKET_TAG-py3-none-any.whl /dtlpy-$BITBUCKET_TAG-py3-none-any.whl
RUN mkdir -p /src
ENV PYTHONPATH="$PYTHONPATH:/src"
RUN pip install --no-cache-dir --target=/src /dtlpy-$BITBUCKET_TAG-py3-none-any.whl --upgrade
