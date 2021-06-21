FROM python:3.8.11-slim
COPY . /tmp/src
RUN cd /tmp/src \
    && python3 setup.py install \
    && cd / \
    && rm -rf /tmp/src

ARG BUILD_DATE
ARG BUILD_TAG
ARG BASE_IMAGE_TAG

ENV CLDR_BUILD_DATE=${BUILD_DATE}
ENV CLDR_BUILD_VER=${BUILD_TAG}

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
