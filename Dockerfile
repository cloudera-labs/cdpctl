FROM python:3.9.7-slim
ARG BUILD_DATE
ARG BUILD_TAG
ARG BASE_IMAGE_TAG
ARG APPLICATION_VERSION

ENV CLDR_BUILD_DATE=${BUILD_DATE}
ENV CLDR_BUILD_VER=${BUILD_TAG}

ENV CDPCTL_APPLICATION_VERSION=${APPLICATION_VERSION}
COPY . /tmp/src

RUN cd /tmp/src \
    && pip3 --no-cache-dir install azure-cli==2.28.0 \
    && echo "\"\"\"Version info.\"\"\"" > cdpctl/__version__.py \
    && echo "__version__ = \"${CDPCTL_APPLICATION_VERSION}\"" >> cdpctl/__version__.py \
    && rm -rf /var/lib/apt/lists/* \
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
