# Base Image: Python 3.11 (Debian Bullseye)
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install Google Cloud SDK
# We add the official Google Cloud APT repo and install the CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get install -y google-cloud-cli

# Verify installation
RUN gcloud --version