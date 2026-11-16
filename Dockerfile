FROM python:3.10

ARG SDK_VERSION
ADD ./dist/dtlpy-$SDK_VERSION-py3-none-any.whl /dtlpy-$SDK_VERSION-py3-none-any.whl
RUN mkdir -p /src
ENV PYTHONPATH="$PYTHONPATH:/src"
RUN pip install --no-cache-dir --target=/src /dtlpy-$SDK_VERSION-py3-none-any.whl --upgrade
