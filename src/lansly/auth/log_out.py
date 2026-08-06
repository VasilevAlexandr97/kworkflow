from lansly.auth.interfaces import SessionManager


class LogOut:
    def __init__(self, auth_session_manager: SessionManager):
        self.auth_session_manager = auth_session_manager

    async def invalidate(self):
        await self.auth_session_manager.clear_session()
