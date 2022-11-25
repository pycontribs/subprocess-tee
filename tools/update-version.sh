#!/bin/bash
DIR=$(dirname "$0")
VERSION=$(./tools/get-version.sh)
mkdir -p "${DIR}/../dist"
sed -e "s/VERSION_PLACEHOLDER/${VERSION}/" \
    "${DIR}/../.config/subprocess-tee.spec" \
    > "${DIR}/../dist/subprocess-tee.spec"
