from app.modules.metrics.infrastructure.repositories.metrics_repository import MetricsRepository
from app.modules.metrics.domain.entities.schemas import GlobalMetricsResponse

class GetGlobalMetricsUseCase:
    def __init__(self, repo: MetricsRepository):
        self.repo = repo

    def execute(self) -> GlobalMetricsResponse:
        return GlobalMetricsResponse(
            total_meters=self.repo.get_total_meters(),
            online_meters=self.repo.get_online_meters(),
            today_revenue=self.repo.get_today_revenue(),
            failed_commands=self.repo.get_failed_commands(),
            avg_latency_ms=self.repo.get_avg_latency()
        )
