FROM python:3.10.0-alpine3.13

WORKDIR /app

COPY src/. .

RUN adduser -D speedtest
RUN apk --update add iperf3 && \
    rm -rf /var/cache/apk/*
RUN pip install -r requirements.txt && \
    rm requirements.txt

RUN chown -R speedtest:speedtest /app

USER speedtest

CMD ["python", "-u", "iperf3_speed_exporter.py"]

HEALTHCHECK --timeout=10s CMD wget --no-verbose --tries=1 --spider http://localhost:${SPEEDTEST_PORT:=9798}/