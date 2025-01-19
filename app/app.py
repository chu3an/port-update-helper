import os
import logging
from qbapi import QBAPI
from gtapi import GTAPI
from flask import Flask

QB_URL = os.getenv('QB_URL', 'ERROR')
QB_USERNAME = os.getenv('QB_USERNAME', 'ERROR')
QB_PASSWORD = os.getenv('QB_PASSWORD', 'ERROR')
GT_URL = os.getenv('GT_URL', 'ERROR')
GT_USERNAME = os.getenv('GT_USERNAME', 'ERROR')
GT_PASSWORD = os.getenv('GT_PASSWORD', 'ERROR')
app = Flask(__name__)


class cLOG:
    def __init__(self, name, level='INFO'):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)
        log_fmt = '%(asctime)s %(levelname)s: %(message)s'
        date_fmt = '%Y-%m-%d %H:%M:%S'
        self._formatter = logging.Formatter(fmt=log_fmt, datefmt=date_fmt)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(self._formatter)
        self._logger.addHandler(stream_handler)

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)


@app.route('/', methods=['POST'])
def post_change_port():
    log.info('Receive post -> change_port')
    change_port()
    return "OK", 200


def change_port(bypass=False):
    qb.login()
    if qb_port := qb.get_port():
        log.info(f'qBittorrent listen port {qb_port}')
    else:
        log.error(f'qBittorrent port check fail')
        exit(1)
    port_data = gt.get_fowarded_port()
    if not port_data:
        log.error(f'Gluetun API get-port fail, please check your environment')
        exit(1)
    gt_port = port_data['port']
    log.info(f'Gluetun forwarded port {gt_port}')
    if qb_port != gt_port:
        qb.set_port(port=gt_port)
        qb_port = qb.get_port()
        log.info(f'qBittorrent listen port {qb_port} (changed)')
    else:
        log.info(f'Port unchanged (same number)')
    qb.logout()


if __name__ == '__main__':
    # log initial
    log = cLOG('port-update-helper', level='INFO')

    # check environment variables
    for i in [QB_URL, QB_USERNAME, QB_PASSWORD, GT_URL, GT_USERNAME, GT_PASSWORD]:
        if i == 'ERROR':
            log.error(f'Environment variables error, please check your setting')
            exit(1)

    # check qbittorrent
    qb = QBAPI(QB_URL, QB_USERNAME, QB_PASSWORD)
    result = qb.login()
    if not result:
        log.error(f'qbittorrent login fail, please check your environment')
        exit(1)
    if qb_vers := qb.get_version():
        log.info(f'qBittorrent version {qb_vers}')
    else:
        log.error(f'qBittorrent version check fail')
        exit(1)
    qb.logout()

    # check gluetun
    gt = GTAPI(GT_URL, GT_USERNAME, GT_PASSWORD)
    ip_data = gt.get_public_ip()
    if not ip_data:
        log.error(f'Gluetun API get-ip fail, please check your environment')
        exit(1)
    ip = ip_data['public_ip']
    location = ip_data['country']+'-'+ip_data['city']
    log.info(f'Gluetun public ip {ip} ({location})')

    change_port()
    app.run(host='0.0.0.0', port=9080, debug=False)
