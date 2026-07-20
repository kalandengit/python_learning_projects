FROM python:3.12-slim

# Create kalanfa user and group (no home dir, /kalanfa is used as KALANFA_HOME)
RUN groupadd --gid 1000 kalanfa \
    && useradd --uid 1000 --gid kalanfa --shell /bin/bash kalanfa

# Create /kalanfa directory with proper ownership
RUN mkdir /kalanfa && chown kalanfa:kalanfa /kalanfa

# Install Kalanfa from PyPI
ARG KALANFA_VERSION
ARG KALANFA_VERSION_SPEC
RUN pip install --no-cache-dir kalanfa${KALANFA_VERSION_SPEC}

# Copy entrypoint script with executable permissions
COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY README.md /README.md

# Expose ports
EXPOSE 8080 8081

# Set environment variables
ENV KALANFA_VERSION="${KALANFA_VERSION}"
ENV KALANFA_HOME=/kalanfa
ENV KALANFA_HTTP_PORT=8080
ENV KALANFA_ZIP_CONTENT_PORT=8081

WORKDIR /kalanfa

ENTRYPOINT ["/entrypoint.sh"]
CMD ["kalanfa", "start", "--foreground"]
