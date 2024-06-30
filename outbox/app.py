import asyncio
import sys
import time
from contextlib import asynccontextmanager
from functools import partial

import uvicorn
from apscheduler import Scheduler
from dependency_injector.wiring import inject, Provide
from fastapi import FastAPI, Depends
from outbox.dependecies import DependencyContainer, container
from outbox.jobs import publish_job
from outbox.middleware import SchedulerMiddleware
from outbox.model import OutBox, MessageStatus
from outbox.service import OutBoxService


@inject
def create_app(_scheduler_app: Scheduler = Provide[DependencyContainer.scheduler_app],
               _service: OutBoxService = Provide[DependencyContainer.service]):
    f_app = FastAPI()
    f_app._service = _service
    f_app.add_middleware(SchedulerMiddleware,
                         scheduler=_scheduler_app,
                         task=publish_job,
                         container=container
                         )
    return f_app


container.wire(modules=[__name__])

app = create_app()


@app.post("/add-meesage")
async def main(routing_key: str,
               queue_name: str = "outbox",
               exchange_name: str = "outbox"):
    await app._service.add_message(
        OutBox(data={'hello': 'world'},
               routing_key=routing_key,
               queue_name=queue_name,
               exchange_name=exchange_name))
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, lifespan="on")
