FROM alpine:latest
# Alpine is used on purpose because it does not come with bash, and we
# want to test that subprocess-tee works even on systems without bash shell.
ENV BUILD_DEPS="\
ansible-base \
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
${BUILD_DEPS} && \
pip3 install -U pip

COPY . /root/code/
WORKDIR /root/code/
RUN \
python3 --version && \
python3 -m pip install ".[test]" && \
python3 -m pytest
