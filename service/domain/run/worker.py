import logging
import time
from datetime import datetime, timezone
from typing import Optional

from domain.run.executor import RunExecutor
from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository

logger = logging.getLogger(__name__)


class RunWorker:
    def __init__(self, repo: AbstractRunRepository, executor: RunExecutor, poll_interval: float = 5.0) -> None:
        self._repo = repo
        self._executor = executor
        self._poll_interval = poll_interval

    def run(self) -> None:
        logger.info("Worker started")
        while True:
            self._tick()

    def _tick(self) -> None:
        run = self._repo.claim_oldest_queued()
        if run is None:
            time.sleep(self._poll_interval)
            return

        logger.info("Starting run %s", run.id)
        run = self._repo.update(Run(
            **{**run.__dict__, "status": RunStatus.running, "started_at": datetime.now(timezone.utc)}
        ))
        try:
            result = self._executor.execute(run)
            if result.success:
                self._repo.update(Run(
                    **{**run.__dict__, "status": RunStatus.completed, "completed_at": datetime.now(timezone.utc)}
                ))
                logger.info("Completed run %s", run.id)
            else:
                self._fail(run, result.error_message)
        except Exception as e:
            self._fail(run, str(e))

    def _fail(self, run: Run, error_message: Optional[str]) -> None:
        self._repo.update(Run(
            **{**run.__dict__, "status": RunStatus.failed, "completed_at": datetime.now(timezone.utc),
               "error_message": error_message}
        ))
        logger.error("Failed run %s: %s", run.id, error_message)
