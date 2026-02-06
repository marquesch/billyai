from domain.ports.services import AsyncTaskDispatcherService


class AsyncTask:
    @classmethod
    async def dispatch(cls, async_task_dispatcher_service: AsyncTaskDispatcherService, **kwargs):
        await async_task_dispatcher_service.dispatch(cls.__name__, **kwargs)
