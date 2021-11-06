#!/usr/bin/python

import iperf3
import os
import datetime
from prometheus_client import make_wsgi_app, Gauge
from waitress import serve
from flask import Flask
from pprint import pformat
from logging.config import dictConfig

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask("Iperf3-Speed-Exporter")  # Create flask app

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
app.logger.setLevel(level=LOGLEVEL)

# Create metrics
download_speed = Gauge(
    "speedtest_download_Mbps", "Speedtest current Download Speed in Mb/s"
)
upload_speed = Gauge("speedtest_upload_Mbps", "Speedtest current Upload speed in Mb/s")
up = Gauge("speedtest_up", "Speedtest status whether the scrape worked")


def run_test(mode):
    client = iperf3.Client()
    if mode == "download":
        client.reverse = True
    elif mode == "upload":
        client.reverse = False
    else:
        raise Exception("mode needs to be one of [upload, download]")

    client.duration = os.getenv("SPEEDTEST_DURATION", 10)
    client.server_hostname = os.getenv(
        "SPEEDTEST_SERVER_HOSTNAME", "speedtest.wtnet.de"
    )
    client.port = os.getenv("SPEEDTEST_SERVER_PORT", 5202)
    client.protocol = os.getenv("SPEEDTEST_PROTOCOL", "tcp")
    app.logger.info(f"Running {mode} test")
    app.logger.debug("Test parameter")
    app.logger.debug(pformat(client.__dict__))

    result = client.run()

    try:
        # result.pop(received_Mbps)
        return (result.received_Mbps, 1)
    except AttributeError as e:
        app.logger.error(str(e))
        return (0, 0)


@app.route("/run_test")
def run_tests():
    r_download_speed, r_status = run_test(mode="download")
    r_upload_speed, r_status = run_test(mode="upload")
    download_speed.set(r_download_speed)
    upload_speed.set(r_upload_speed)
    up.set(r_status)
    current_dt = datetime.datetime.now()
    app.logger.info(
        current_dt.strftime("%d/%m/%Y %H:%M:%S - ")
        + " Download[Mbps]: "
        + str(r_download_speed)
        + " | Upload[Mbps]: "
        + str(r_upload_speed)
    )
    return make_wsgi_app()


@app.route("/")
def mainPage():
    return (
        "<h1>Welcome to Iperf3-Speed-Exporter.</h1>"
        + "Click <a href='/run_test'>here</a> to start a speed test."
    )


if __name__ == "__main__":
    PORT = os.getenv("SPEEDTEST_PORT", 9798)
    app.logger.info("Starting Speedtest-Exporter on http://localhost:" + str(PORT))
    serve(app, host="0.0.0.0", port=PORT)
