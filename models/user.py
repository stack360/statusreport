"""User Model Handler."""
import crypt
import models
import datetime

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


def upsert_token(user, duration):
    expire_timestamp = datetime.datetime.now() + duration
    token_str = _encrypt(user.username)
    if user.token:
        token_object = models.Token.objects.get(token=user.token.token)
    else:
        token_object = models.Token()
    token_object.token = token_str
    token_object.expire_timestamp = expire_timestamp
    token_object.save()

    return token_object

def extend_token(user, duration):
    expire_timestamp = user.token.expire_timestamp + duration
    token_object = models.Token.objects.get(token=user.token.token)
    token_object.expire_timestamp = expire_timestamp
    token_object.save()
    return token_object

def get_auth_token(username):
    return _encrypt(username)
