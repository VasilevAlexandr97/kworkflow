from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.common.interfaces.transaction_manager import TransactionManager


class SATransactionManager(TransactionManager):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        await self.session.commit()

    async def flush(self):
        await self.session.flush()

    async def rollback(self):
        await self.session.rollback()
