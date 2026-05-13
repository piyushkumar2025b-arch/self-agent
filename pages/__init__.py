"""
pages/__init__.py
All page modules expose a render() function called by connector.route().
"""
__all__ = [
    "agents", "analytics", "api_config", "batch_runner", "cost_tracker",
    "dashboard", "diff_viewer", "grammar_emoji", "image_generator",
    "knowledge_base", "logs", "memory_viewer", "model_playground",
    "pipeline_studio", "pipelines", "pipelines_v2", "prompt_library",
    "scheduler", "settings", "sound_gen_page", "tools_tester",
    "web_wiki", "youtube_tools",
]
