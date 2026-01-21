import os
import logging
import sys
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response

# Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
log = logging.getLogger("port-update-helper")

# Environment Variables
QB_URL = os.getenv('QB_URL', 'ERROR')
QB_USERNAME = os.getenv('QB_USERNAME', 'ERROR')
QB_PASSWORD = os.getenv('QB_PASSWORD', 'ERROR')
GT_URL = os.getenv('GT_URL', 'ERROR')
GT_USERNAME = os.getenv('GT_USERNAME', 'ERROR')
GT_PASSWORD = os.getenv('GT_PASSWORD', 'ERROR')

class QBAPI:
    def __init__(self, url, username, password):
        self.session = requests.Session()
        self.baseurl = url
        self.username = username
        self.password = password

    def login(self):
        url = f'{self.baseurl}/api/v2/auth/login'
        data = {
            'username': self.username,
            'password': self.password
        }
        r = self.session.post(url, data=data)
        if r.status_code == 200 and r.text == 'Ok.':
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
        r = requests.get(f'{self.url}/v1/publicip/ip', auth=(self.username, self.password))
        if r.status_code == 200:
            return r.json()
        else:
            return False

    def get_fowarded_port(self):
        # Updated Endpoint: /v1/openvpn/portforwarded -> /v1/portforward
        r = requests.get(f'{self.url}/v1/portforward', auth=(self.username, self.password))
        if r.status_code == 200:
            return r.json()
        else:
            return False

# Global instances
qb = None
gt = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global qb, gt
    
    # Check environment variables
    env_vars = [QB_URL, QB_USERNAME, QB_PASSWORD, GT_URL, GT_USERNAME, GT_PASSWORD]
    if 'ERROR' in env_vars:
        log.error('Environment variables error, please check your setting')
        sys.exit(1)

    # Initialize APIs
    qb = QBAPI(QB_URL, QB_USERNAME, QB_PASSWORD)
    gt = GTAPI(GT_URL, GT_USERNAME, GT_PASSWORD)

    # Check qBittorrent connection
    if not qb.login():
        log.error('qBittorrent login fail, please check your environment')
        sys.exit(1)
    
    if qb_vers := qb.get_version():
        log.info(f'qBittorrent version {qb_vers}')
    else:
        log.error('qBittorrent version check fail')
        sys.exit(1)
    qb.logout()

    # Check Gluetun connection
    ip_data = gt.get_public_ip()
    if not ip_data:
        log.error('Gluetun API get-ip fail, please check your environment')
        sys.exit(1)
    
    ip = ip_data.get('public_ip', 'Unknown')
    country = ip_data.get('country', 'Unknown')
    city = ip_data.get('city', 'Unknown')
    log.info(f'Gluetun public ip {ip} ({country}-{city})')

    # Initial port update
    change_port()
    
    yield
    # Shutdown logic (if any)

app = FastAPI(lifespan=lifespan)

def change_port():
    qb.login()
    qb_port = qb.get_port()
    
    if qb_port:
        log.info(f'qBittorrent listen port {qb_port}')
    else:
        log.error('qBittorrent port check fail')
        qb.logout()
        return False

    port_data = gt.get_fowarded_port()
    if not port_data:
        log.error('Gluetun API get-port fail, please check your environment')
        qb.logout()
        return False

    gt_port = port_data['port']
    
    # Safety Check: Gluetun returning 0
    if gt_port <= 0:
        log.error(f'Invalid Gluetun port detected: {gt_port}. Aborting update to prevent configuration corruption.')
        qb.logout()
        return False

    log.info(f'Gluetun forwarded port {gt_port}')
    
    if qb_port != gt_port:
        if qb.set_port(port=gt_port):
            # Verify change
            new_qb_port = qb.get_port()
            log.info(f'qBittorrent listen port {new_qb_port} (changed)')
        else:
            log.error('Failed to update qBittorrent port')
    else:
        log.info('Port unchanged (same number)')
    
    qb.logout()
    return True

@app.post("/")
async def post_change_port():
    log.info('Receive post -> change_port')
    success = change_port()
    if not success:
        return Response(content="Update Failed", status_code=500)
    return Response(content="OK", status_code=200)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=9080)
