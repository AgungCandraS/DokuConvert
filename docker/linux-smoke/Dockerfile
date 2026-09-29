FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    QT_QPA_PLATFORM=offscreen

WORKDIR /tmp
COPY DocuConvert.deb /tmp/DocuConvert.deb

RUN apt-get update \
    && apt-get install --yes --no-install-recommends /tmp/DocuConvert.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/DocuConvert.deb

CMD ["/bin/sh", "-ec", "app=/opt/docuconvert/DocuConvert/DocuConvert; QT_QPA_PLATFORM=offscreen \"$app\" >/tmp/docuconvert.log 2>&1 & app_pid=$!; trap 'kill \"$app_pid\" 2>/dev/null || true; wait \"$app_pid\" 2>/dev/null || true' EXIT; sleep 12; kill -0 \"$app_pid\" || { cat /tmp/docuconvert.log; exit 1; }"]
