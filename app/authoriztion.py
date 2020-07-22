from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class AuthSigner(object):
    """Signer for use with authenticated ADB, introduced in 4.4.x/KitKat."""

    def sign(self, data):
        """Signs given data using a private key."""
        raise NotImplementedError()

    def get_public_key(self):
        """Returns the public key in PEM format without headers or newlines."""
        raise NotImplementedError()


class CryptoAuthSigner(AuthSigner):

    def get_public_key(self):
        return self.public_key

    def __init__(self, rsa_key_path=None):
        if rsa_key_path:
            with open(rsa_key_path + '.pub', 'rb') as rsa_pub_file:
                self.public_key = rsa_pub_file.read()

            with open(rsa_key_path, 'rb') as rsa_priv_file:
                self.rsa_key = RSA.import_key(rsa_priv_file.read())

    def sign(self, data):
        h = SHA256.new(data)
        return pkcs1_15.new(self.rsa_key).sign(h)
