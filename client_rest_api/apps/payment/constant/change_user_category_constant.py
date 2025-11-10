from functools import wraps


def check_and_update_user_category(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        
        isGCC = request.query_params.get('isGCC')
        if not isGCC:
            userToken = request.headers.get('Auth-Token')
            pass

    
        return view_func(self, request, *args, **kwargs)
         
    
    return wrapped_view
