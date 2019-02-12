#!/bin/sh

docker build -t gcr.io/viewo-g/sdk-gpu:$1 -f ./Dockerfile.gpu --build-arg BITBUCKET_TAG=$1 .
docker tag gcr.io/viewo-g/sdk-gpu:$1 gcr.io/viewo-g/sdk-gpu:latest

docker push gcr.io/viewo-g/sdk-gpu:$1
docker push gcr.io/viewo-g/sdk-gpu:latest