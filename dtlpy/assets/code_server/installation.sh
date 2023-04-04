#!/bin/bash
cd /tmp/app

PORT=${1?}

# check if curl command exists
if ! command -v curl &> /dev/null
then
    echo "curl could not be found. installing..."
    apt update -y
    apt install -y curl
fi

# check if code-server command exists
if ! command -v code-server &> /dev/null
then
    echo "code-server could not be found. installing..."
    bash <(curl -s https://raw.githubusercontent.com/coder/code-server/main/install.sh)
    code-server --install-extension ms-python.python
    code-server --install-extension okteto.remote-kubernetes
    code-server --install-extension ms-vscode-remote.vscode-remote-extensionpack
    code-server --install-extension ms-vscode-remote.remote-containers
    code-server --install-extension ms-vscode-remote.remote-wsl
fi
code-server --bind-addr 0.0.0.0:${PORT} --auth none --cert false /tmp/app