# cspell: ignore ruamel
FROM alpine:latest
# Alpine is used on purpose because it does not come with bash, and we
# want to test that subprocess-tee works even on systems without bash shell.
ENV BUILD_DEPS="\
ansible-core \
gcc \
git \
libffi-dev \
make \
musl-dev \
python3 \
python3-dev \
py3-pip \
py3-ruamel.yaml \
"

RUN \
apk add --update --no-cache \
${BUILD_DEPS}

COPY . /root/code/
WORKDIR /root/code/
RUN \
python3 --version && \
python3 -m venv venv && \
. venv/bin/activate && \
python3 -m pip install ".[test]" && \
python3 -m pytest
