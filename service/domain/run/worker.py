import time
from datetime import datetime, timezone

from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository


class RunWorker:
    def __init__(self, repo: AbstractRunRepository, poll_interval: float = 5.0) -> None:
        self._repo = repo
        self._poll_interval = poll_interval

    def run(self) -> None:
        while True:
            run = self._repo.claim_oldest_queued()
            if run is None:
                time.sleep(self._poll_interval)
                continue

            run = self._repo.update(Run(
                **{**run.__dict__, "status": RunStatus.running, "started_at": datetime.now(timezone.utc)}
            ))
            try:
                # NOP
                self._repo.update(Run(
                    **{**run.__dict__, "status": RunStatus.completed, "completed_at": datetime.now(timezone.utc)}
                ))
            except Exception as e:
                self._repo.update(Run(
                    **{**run.__dict__, "status": RunStatus.failed, "completed_at": datetime.now(timezone.utc),
                       "error_message": str(e)}
                ))
