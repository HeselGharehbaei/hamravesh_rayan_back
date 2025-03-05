import threading

# Thread-local storage for user
_thread_locals = threading.local()

def get_current_user():
    """Retrieve the stored user from thread-local storage."""
    return getattr(_thread_locals, "user", None)

class CurrentUserMiddleware:
    """Middleware to store the request user in thread-local storage."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user  # Store user in thread-local storage
        response = self.get_response(request)
        return response

