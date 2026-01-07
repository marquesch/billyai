from infrastructure.async_tasks import async_task


@async_task
async def notify_user(message_id: int):
    # TODO: notify user using websocket
    return
