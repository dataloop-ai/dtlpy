#!/bin/sh

docker build -t gcr.io/viewo-g/sdk:$1 -f ./Dockerfile --build-arg BITBUCKET_TAG=$1 .
docker tag gcr.io/viewo-g/sdk:$1 gcr.io/viewo-g/sdk:latest

docker push gcr.io/viewo-g/sdk:$1
docker push gcr.io/viewo-g/sdk:latest


docker build -t gcr.io/viewo-g/sdk-docs:$1 -f ./Dockerfile.docs .
docker tag gcr.io/viewo-g/sdk-docs:$1 gcr.io/viewo-g/sdk-docs:latest

docker push gcr.io/viewo-g/sdk-docs:$1
docker push gcr.io/viewo-g/sdk-docs:latest