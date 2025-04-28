# Moved decorators to a separate module
from functools import wraps
from flask import request, redirect, url_for

def require_cookie(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if not check_user_cookie():
            return redirect(url_for('routes.register'))
        return view_func(*args, **kwargs)
    return decorated_function

def check_user_cookie():
    return 'username' in request.cookies