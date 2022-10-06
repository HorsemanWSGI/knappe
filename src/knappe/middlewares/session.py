import itsdangerous
import typing as t
from http_session.meta import Store
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from knappe.request import WSGIRequest
from knappe.response import Response
from knappe.types import Handler


class HTTPSession:

    manager: SignedCookieManager

    class Configuration(t.NamedTuple):
        store: Store
        secret: str
        samesite: SameSite = SameSite.lax
        httponly: bool = True
        digest: str = HashAlgorithm.sha1.name
        TTL: int = 300
        cookie_name: str = 'sid'
        secure: bool = True
        salt: t.Optional[str] = None
        save_new_empty: bool = False

    def __init__(self, *args, **kwargs):
        self.config = self.Configuration(*args, **kwargs)
        self.manager = SignedCookieManager(
            self.config.store,
            self.config.secret,
            salt=self.config.salt,
            digest=self.config.digest,
            TTL=self.config.TTL,
            cookie_name=self.config.cookie_name,
        )

    def __call__(self,
                 handler: Handler[WSGIRequest, Response],
                 globalconf: t.Optional[t.Mapping] = None
                 ) -> Handler[WSGIRequest, Response]:

        def http_session_middleware(request: WSGIRequest) -> Response:
            session = request.context.get('http_session')
            if session is None:
                new = True
                if request.environ.cookies and (
                        sig := request.environ.cookies.get(
                            self.manager.cookie_name)):
                    try:
                        sid = str(self.manager.verify_id(sig), 'utf-8')
                        new = False
                    except itsdangerous.exc.SignatureExpired:
                        # Session expired. We generate a new one.
                        pass
                    except itsdangerous.exc.BadTimeSignature:
                        # Discrepancy in time signature.
                        # Invalid, generate a new one
                        pass

                if new is True:
                    sid = self.manager.generate_id()

                session = self.manager.session_factory(
                    sid, self.manager.store, new=new
                )
                request.context['http_session'] = session

            response = handler(request)

            if not session.modified and (
                    session.new and self.config.save_new_empty):
                session.save()

            if session.modified:
                if response.status < 400:
                    tm = request.context.get('transaction_manager')
                    if tm is None or not tm.isDoomed():
                        session.persist()
            elif session.new:
                return response

            domain = request.environ['HTTP_HOST'].split(':', 1)[0]
            cookie = self.manager.cookie(
                session.sid,
                request.environ.script_name or '/',
                domain,
                secure=self.config.secure,
                samesite=self.config.samesite,
                httponly=self.config.httponly
            )
            response.cookies[self.manager.cookie_name] = cookie
            return response

        return http_session_middleware
