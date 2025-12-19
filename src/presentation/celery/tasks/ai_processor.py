from infrastructure.services.ai_service import AIService
from presentation.celery.tasks import DITask


class AITask(DITask):
    dependencies = [AIService]
