import os
import requests
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from flask import Flask

QB_URL = os.getenv('QB_URL', 'ERROR')
QB_USERNAME = os.getenv('QB_USERNAME', 'ERROR')
QB_PASSWORD = os.getenv('QB_PASSWORD', 'ERROR')
GT_URL = os.getenv('GT_URL', 'ERROR')
GT_USERNAME = os.getenv('GT_USERNAME', 'ERROR')
GT_PASSWORD = os.getenv('GT_PASSWORD', 'ERROR')

class cLOG:
    def __init__(self, name, level='INFO'):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self._t2l(level))
        self._formatter = logging.Formatter(
            fmt='%(asctime)s %(name)s %(levelname)s: %(message)s')

    def _t2l(self, level: str) -> int:
        if level.upper() == 'DEBUG':
            return logging.DEBUG
        elif level.upper() == 'INFO':
            return logging.INFO
        elif level.upper() == 'WARNING':
            return logging.WARNING
        elif level.upper() == 'ERROR':
            return logging.ERROR
        else:
            return logging.ERROR
        

    def add_stream_handler(self, level='INFO'):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self._t2l(level))
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


class QBAPI:
    def __init__(self, url):
        self.session = requests.Session()
        self.baseurl = url

    def login(self, username, password):
        url = f'{self.baseurl}/api/v2/auth/login'
        data = {
            'username': username,
            'password': password
        }
        r = self.session.post(url, data=data)
        if r.status_code == 200:
            return True
        else:
            return False

    def logout(self):
        url = f'{self.baseurl}/api/v2/auth/login'
        r = self.session.post(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def get_version(self):
        url = f'{self.baseurl}/api/v2/app/version'
        r = self.session.get(url)
        if r.status_code == 200:
            return r.text.strip()
        else:
            return False

    def get_port(self, key=None):
        url = f'{self.baseurl}/api/v2/app/preferences'
        r = self.session.get(url)
        if r.status_code == 200:
            data = r.json()
            return data['listen_port']
        else:
            return False

    def set_port(self, port):
        url = f'{self.baseurl}/api/v2/app/setPreferences'
        data = {'json': '{\"listen_port\": %d}' % port}
        r = self.session.post(url, data=data)
        if r.status_code == 200:
            return True
        else:
            return False


class GTAPI:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

    def get_public_ip(self):
        r = requests.get(f'{GT_URL}/v1/publicip/ip',auth=(GT_USERNAME, GT_PASSWORD))
        if r.status_code == 200:
            return r.json()
        else:
            return False

    def get_fowarded_port(self):
        r = requests.get(f'{GT_URL}/v1/openvpn/portforwarded',auth=(GT_USERNAME, GT_PASSWORD))
        if r.status_code == 200:
            return r.json()
        else:
            return False

app = Flask(__name__)

@app.route('/', methods=['POST'])
def on_change_port():
    log.info('Receive post -> change qbittorrent port')
    qb.login(username=QB_USERNAME, password=QB_PASSWORD)
    qb_port = qb.get_port()
    log.info(f'qBittorrent port before change -> {qb_port}')
    port_data = gt.get_fowarded_port()
    gt_port = port_data['port']
    log.info(f'Gluetun port -> {gt_port}')
    qb.set_port(port=gt_port)
    qb_port = qb.get_port()
    log.info(f'qBittorrent port after change -> {qb_port}')
    return "OK", 200


if __name__ == '__main__':
    # log initial
    log = cLOG('PORT-MATE', level='INFO')
    log.add_stream_handler()
    
    # check qbittorrent
    log.info('Starting program')
    log.info('Checking qbittorrent environment')
    for i in [QB_URL, QB_USERNAME, QB_PASSWORD]:
        if i == 'ERROR':
            log.error(f'qbittorrent variable error, please check your environment')
            exit(1)
    qb = QBAPI(url=QB_URL)
    result = qb.login(username=QB_USERNAME, password=QB_PASSWORD)
    if not result: 
        log.error(f'qbittorrent login fail, please check your environment')
    qb_vers = qb.get_version()
    if qb_vers:
        log.info(f'qBittorrent version {qb_vers}')
    else:
        log.info(f'qBittorrent version check fail')
    qb_port = qb.get_port()
    if qb_port:
        log.info(f'qBittorrent port {qb_port}')
    else:
        log.info(f'qBittorrent port check fail')

    # check gluetun
    log.info('Checking gluetun environment')
    for i in [GT_URL, GT_USERNAME, GT_PASSWORD]:
        if i == 'ERROR':
            log.error(f'gluetun variable error, please check your environment')
            exit(1)
    gt = GTAPI(GT_URL, GT_USERNAME, GT_PASSWORD)
    ip_data = gt.get_public_ip()
    if not ip_data:
        log.error(f'Gluetun API get-ip fail, please check your environment')
        exit(1)
    ip = ip_data['public_ip']
    location = ip_data['country']+'-'+ip_data['city']
    log.info(f'Gluetun: public ip -> {ip}')
    log.info(f'Gluetun: public location -> {location}')
    port_data = gt.get_fowarded_port()
    if not port_data:
        log.error(f'Gluetun API get-port fail, please check your environment')
        exit(1)
    port = port_data['port']
    log.info(f'Gluetun: public ip -> {port_data}')

    app.run(host='0.0.0.0', port=9080, debug=False)
