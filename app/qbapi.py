import requests


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
