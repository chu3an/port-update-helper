import requests


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
        r = requests.get(f'{self.url}/v1/openvpn/portforwarded', auth=(self.username, self.password))
        if r.status_code == 200:
            return r.json()
        else:
            return False
