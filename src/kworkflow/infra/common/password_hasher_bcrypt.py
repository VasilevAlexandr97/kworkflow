import bcrypt

from kworkflow.common.interfaces.password_hasher import PasswordHasher


class PasswordHasherBcrypt(PasswordHasher):
    def hash(self, password: str) -> str:
        pw_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        )
        return pw_hash.decode("utf-8")

    def verify(
        self,
        password: str,
        hashed_password: str,
    ) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
