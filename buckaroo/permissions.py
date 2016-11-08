from rest_framework.permissions import BasePermission


class PostOnly(BasePermission):
    """
    Only POST requests are allowed.
    """
    message = 'Only POST requests allowed.'

    def has_permission(self, request, view):
        return request.method == "POST"


class BuckarooServer(BasePermission):
    """
    Buckaroo does a POST with transaction data.
    """
    message = "Only Buckaroo server may do a push update."

    def has_permission(self, request, view):

        try:
            host = request.META['HTTP_HOST']
        except KeyError:
            return False

        for item in ["localhost", "ngrok", "buckaroo"]:
            if item in host:
                return True
        return False
