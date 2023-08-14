from horseman.environ import Environ
from knappe.response import Response


class APIView:
    """View with methods to act as HTTP METHOD dispatcher.
    Method names of the class must be a valid uppercase HTTP METHOD name.
    example : OPTIONS, GET, POST
    """

    def __call__(self, environ: Environ) -> Response:
        method = environ['REQUEST_METHOD'].upper()
        if worker := getattr(self, method, None):
            return worker(environ)

        # Method not allowed
        return Response(405)
