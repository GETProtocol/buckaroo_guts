import base64
import hmac
import hashlib
import urllib.parse
import random
import json
import time

from django.conf import settings


def generate_nonce(length=8):
    """Generate pseudorandom number."""
    result = ''.join([str(random.randint(0, 9)) for i in range(length)])
    return result


def generate_timestamp():
    """Generate timestamp."""
    result = int(time.time())
    return result


def get_json_md5_digest(json_data=None):
    """Generate MD5 digest from a JSON encoded string."""
    data = json.dumps(json_data).encode('utf-8')
    m = hashlib.md5(data)
    return m.digest()


class AuthHeader:
    def __init__(self, transaction=None, url=None, json=None, method="POST"):
        self.json = json
        self.url = url

        self.transaction = transaction
        self.auth_header = None
        self.method = method

    def get_auth_header(self):
        if not self.auth_header:
            return self._generate_auth_header()
        return self.auth_header

    def _get_signature(self,
                       http_method="POST",
                       nonce=None,
                       request_timestamp=None,
                       request_uri=None,
                       json=None):
        """Generate a Base64 hash string for the signature in the authentication header."""

        request_json_base64string = ''

        if json and http_method == 'POST':
            digest = get_json_md5_digest(json_data=json)
            request_json_base64string = base64.b64encode(digest)
            request_json_base64string = request_json_base64string.decode('utf-8')

        msg = self.transaction.order.client.website_key + http_method + \
            request_uri.lower() + \
            str(request_timestamp) + nonce + request_json_base64string

        message = bytes(msg, "utf-8")

        secret = bytes(self.transaction.order.client.secret, "utf-8")

        signature = base64.b64encode(hmac.new(secret,
                                              message,
                                              digestmod=hashlib.sha256).digest())
        return signature

    def _generate_auth_header(self):
        """
        Generate the authentication header to communicate with the
        Buckaroo API.
        """
        from .utils import split_url

        nonce = generate_nonce()
        timestamp = generate_timestamp()
        url = urllib.parse.quote_plus(split_url(self.url))

        signature = self._get_signature(self.method, nonce, timestamp, url, self.json)

        header = "hmac " + self.transaction.order.client.website_key + ":" + \
            signature.decode('utf-8') + ":" + \
            str(nonce) + ":" + str(timestamp)

        self.auth_header = header
        return header
