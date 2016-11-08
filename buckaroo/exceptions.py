from rest_framework.exceptions import APIException


class BuckarooException(Exception):
    """Raise for exceptions from the Buckaroo API"""
    pass


class BuckarooAPIException(APIException):
    """API Exception if anything in the payment service errors."""
    status_code = 500
