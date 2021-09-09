FROM python:3.8.11-slim
ARG BUILD_DATE
ARG BUILD_TAG
ARG BASE_IMAGE_TAG
ARG APPLICATION_VERSION

ENV CLDR_BUILD_DATE=${BUILD_DATE}
ENV CLDR_BUILD_VER=${BUILD_TAG}
ENV CDPCTL_APPLICATION_VERSION=${APPLICATION_VERSION}

COPY . /tmp/src

RUN cd /tmp/src \
    && echo "\"\"\"Version info.\"\"\"" > cdpctl/__version__.py \
    && echo "__version__ = \"${CDPCTL_APPLICATION_VERSION}\"" >> cdpctl/__version__.py \
    && apt update \
    && apt install -y --no-install-recommends ca-certificates curl apt-transport-https lsb-release gnupg \
    && curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
    && export AZ_REPO=$(lsb_release -cs) \
    && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | tee /etc/apt/sources.list.d/azure-cli.list \
    && apt update \
    && apt-get install azure-cli \
    && python3 setup.py install \
    && cd / \
    && rm -rf /tmp/src
# Metadata
LABEL maintainer="Cloudera Labs <cloudera-labs@cloudera.com>" \
      org.label-schema.url="https://github.com/cloudera-labs/cdpctl/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/cloudera-labs/cdpctl/" \
      org.label-schema.build-date="${CLDR_BUILD_DATE}" \
      org.label-schema.version="${CLDR_BUILD_VER}" \
      org.label-schema.vcs-url="https://github.com/cloudera-labs/cdpctl.git" \
      org.label-schema.vcs-ref="https://github.com/cloudera-labs/cdpctl" \
      org.label-schema.docker.dockerfile="/Dockerfile" \
      org.label-schema.description="Validation of the cloud resources for use with the CDP Public Cloud" \
      org.label-schema.schema-version="1.0"

## Set up the execution
CMD ["/usr/local/bin/cdpctl"]
