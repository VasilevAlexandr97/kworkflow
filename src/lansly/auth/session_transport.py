from fastapi import Request

from lansly.auth.interfaces import SessionTransport


class FastAPISessionTransport(SessionTransport):
    def __init__(self, request: Request, session_key: str = "__s_id"):
        self.request = request
        self.session_key = session_key

    def extract_id(self) -> str | None:
        return self.request.session.get(self.session_key)

    def delivery(self, session_id: str) -> None:
        self.request.session[self.session_key] = session_id

    def clear(self) -> None:
        self.request.session.clear()
