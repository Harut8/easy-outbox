from outbox.service import OutBoxService


async def publish_job():
    _service = publish_job.container.service()
    await _service.publish_message()
