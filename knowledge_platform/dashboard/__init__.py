from knowledge_platform.service import KnowledgePlatform


def dashboard(platform: KnowledgePlatform) -> dict[str, object]:
    return {"metrics": platform.metrics.snapshot()}
