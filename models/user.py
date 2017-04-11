"""User Model Handler."""
import crypt
import models

from flask_login import UserMixin

def _encrypt(value, crypt_method=None):
    """Get encrypted value."""
    if not crypt_method:
        if hasattr(crypt, 'METHOD_MD5'):
            crypt_method = crypt.METHOD_MD5
        else:
            # for python2.7, copy python2.6 METHOD_MD5 logic here.
            from random import choice
            import string

            _saltchars = string.ascii_letters + string.digits + './'

            def _mksalt():
                """generate salt."""
                salt = '$1$'
                salt += ''.join(choice(_saltchars) for _ in range(8))
                return salt

            crypt_method = _mksalt()

    return crypt.crypt(value, crypt_method)


def record_user_token(
    token, expire_timestamp, user=None
):
    user = models.User.objects(username=user.username).first()
    user_token = models.Token.objects(user=user.id).first()
    if not user_token:
        user_token = models.Token()
    user_token.key = token
    user_token.expire_timestamp = expire_timestamp
    user_token.user = user
    user_token.save()

    return user_token

def get_auth_token(username):
    return _encrypt(username)
