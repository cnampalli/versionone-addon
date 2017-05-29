from requests.auth import AuthBase
import hmac
import base64
import hashlib
import urlparse
import urllib

class VersionAccessTokenHandler(AuthBase):
    def __init__(self,**args):
        self.access_token = args['access_token']
        
    def __call__(self, r):
        r.headers['Authorization'] = ('Bearer %s' % self.access_token)
        return r