FROM alpine:latest
# Alpine is used on purpose because it does not come with bash, and we
# want to test that subprocess-tee works even on systems without bash shell.
ENV BUILD_DEPS="\
git \
python3 \
py3-pip \
"

RUN \
apk add --update --no-cache \
${BUILD_DEPS}

COPY . /root/code/
WORKDIR /root/code/
RUN \
python3 --version && \
python3 -m pip install ".[test,rich]" && \
python3 -m pytest
