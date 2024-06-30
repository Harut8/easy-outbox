from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send


class SchedulerMiddleware:
    def __init__(
            self,
            app: ASGIApp,
            scheduler: AsyncScheduler,
            container: object = None,
            task=None
    ) -> None:
        self.app = app
        self.scheduler = scheduler
        self.task = task
        self.container = container

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            async with self.scheduler as _secondary_scheduler:
                async with _secondary_scheduler as _main_scheduler:
                    self.task.container = self.container
                    await _main_scheduler.add_schedule(
                        self.task,
                        IntervalTrigger(seconds=1),
                        id=self.task.__name__,
                    )
                    await _main_scheduler.start_in_background()
                    await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)
