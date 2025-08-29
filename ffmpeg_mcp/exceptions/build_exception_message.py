import datetime
import json


def build_exception_message(
	error_type: type,
	message: str,
):
	"""
	Function to build an exception message.

	Params:
	    error_type (type): The python exception class,
	    message (str): The exception message.
	Returns:
	    JSON with structured information about the exception.
	"""
	exception_message = {
		'status': 'ERROR',
		'error_type': error_type.__name__,
		'message': message,
		'time': datetime.datetime.now(datetime.timezone.utc).isoformat()
	}
	return json.dumps(exception_message, indent=2)
