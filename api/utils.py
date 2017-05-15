"""Utilities for  Modulized APIs."""

import exception_handler
import functools
import inspect

import urllib, hashlib
import os, sys
import requests
import random
import datetime

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../../"))
sys.path.append(statusreport_dir)
from statusreport.config import *



def _get_gravatar_url(email):
    default = "http://www.myweeklystatus.com/static/image/e.png"
    default = "404"


    size = 40

    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})

    response = requests.get(gravatar_url)
    if response.status_code == 404:

        return None
    else:
        return gravatar_url

def filetype_allowed(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_LOGO_EXTENSIONS


def supported_filters(
    supported_keys=[],
    optional_supported_keys=[],
    ignored_supported_keys=[],
):
    """Decorator for APIs to filter the input keyword arguments.

    - kwargs that are in ignored_supported_keys are removed.
    - kwargs that are not in these three lists will cause the InvalidParameter
    exception_handler.

    Args:
        supported_keys: these keys must exist.
        optional_supported_keys: these keys are allowed.
        ignored_supported_keys: these keys will be removed.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **filters):
            wrapped_func = get_wrapped_func(func)
            argspec = inspect.getargspec(wrapped_func)
            wrapped_args = argspec.args
            args_defaults = argspec.defaults
            if args_defaults:
                wrapped_must_args = wrapped_args[:-len(args_defaults)]
            else:
                wrapped_must_args = wrapped_args[:]

            # make sure any positional args without default value in
            # decorated function should appear in args or filters.
            if len(args) < len(wrapped_must_args):
                remain_args = wrapped_must_args[len(args):]
                for remain_arg in remain_args:
                    if remain_arg not in filters:
                        raise exception_handler.BadRequest(
                            'function missing declared arg %s '
                            'while caller sends args %s' % (
                                remain_arg, args
                            )
                        )
            # make sure args should be no more than positional args
            # declared in decorated function.
            if len(args) > len(wrapped_args):
                raise exception_handler.BadRequest(
                    'function definition args %s while the caller '
                    'sends args %s' % (
                        wrapped_args, args
                    )
                )

            # exist_args are positional args caller has given.
            exist_args = dict(zip(wrapped_args, args)).keys()
            must_supported_keys = set(supported_keys)
            all_supported_keys = must_supported_keys | set(optional_supported_keys)
            wrapped_supported_keys = set(filters) | set(exist_args)
            unsupported_keys = (
                set(filters) - set(wrapped_args) -
                all_supported_keys - set(ignored_supported_keys)
            )
            # unsupported_keys are the keys that are not in supported_keys,
            # optional_supported_keys, ignored_supported_keys and are not passed in
            # by positional args. It means the decorated function may
            # not understand these parameters.
            if unsupported_keys:
                raise exception_handler.BadRequest(
                    'filter keys %s are not supported for %s' % (
                        list(unsupported_keys), wrapped_func
                    )
                )
            # missing_keys are the keys that must exist but missing in
            # both positional args or kwargs.
            missing_keys = must_supported_keys - wrapped_supported_keys
            if missing_keys:
                raise exception_handler.InvalidParameter(
                    'filter keys %s not found for %s' % (
                        list(missing_keys), wrapped_func
                    )
                )
            # We filter kwargs to eliminate ignored_supported_keys in kwargs
            # passed to decorated function.
            filtered_filters = dict([
                (key, value)
                for key, value in filters.items()
                if key not in ignored_supported_keys
            ])
            return func(*args, **filtered_filters)
        return wrapper
    return decorator


def get_wrapped_func(func):
    """Get wrapped function instance.
    Example:
       @dec1
       @dec2
       myfunc(*args, **kwargs)
       get_wrapped_func(myfunc) returns function object with
       following attributes:
          __name__: 'myfunc'
          args: args
          kwargs: kwargs
       otherwise myfunc is function  object with following attributes:
          __name__: partial object ...
          args: ...
          kwargs: ...
    """
    if func.func_closure:
        for closure in func.func_closure:
            if isfunction(closure.cell_contents):
                return get_wrapped_func(closure.cell_contents)
        return func
    else:
        return func
