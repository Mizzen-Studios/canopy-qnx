FROM --platform=linux/amd64 ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl file binutils build-essential python3 procps unzip xz-utils libgtk-3-0t64 libnss3 libxss1 libasound2t64 libxtst6 libxi6 && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1001 --shell /bin/bash qnx
USER qnx
ENV HOME=/home/qnx
WORKDIR /home/qnx
