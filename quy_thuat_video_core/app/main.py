"""Command-line interface for Quy Thuat Video AI Core V0.1."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config import AppConfig, ConfigError
from app.core.machine import MachineKeyError, verify_machine_key
from app.core.story import StoryCore
from app.core.validator import ValidationError
from app.providers.base import ProviderError
from app.providers.external_provider import ExternalProvider
from app.providers.mock_provider import MockProvider
from app.storage.json_store import StorageError
from app.storage.project import ProjectStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quy Thuat Video AI Core V0.1")
    parser.add_argument("--mock", action="store_true", help="Run without API key using deterministic dummy data")
    parser.add_argument("--project-name", default="Long Thanh Thuc Tinh")
    parser.add_argument("--story-title", default="Long Thanh Thức Tỉnh")
    parser.add_argument("--story-topic", default="A weak young cultivator awakens the bloodline of an ancient dragon.")
    parser.add_argument("--language", default="Vietnamese")
    parser.add_argument("--target-duration", default="5 minutes")
    parser.add_argument("--genre", default="Xianxia / cultivation")
    parser.add_argument("--visual-style", default="Cinematic Chinese fantasy")
    parser.add_argument("--number-of-scenes", type=int, default=3)
    parser.add_argument("--retry-scene", help="Retry one scene ID for an existing project")
    parser.add_argument("--project-dir", help="Existing project directory for retry")
    parser.add_argument("--show-machine-key", action="store_true", help="Print this PC's V0.1 machine key")
    return parser


def select_provider(args: argparse.Namespace, config: AppConfig) -> MockProvider | ExternalProvider:
    """Select the configured provider; called inside main's try/except only."""
    if args.mock:
        return MockProvider()
    return ExternalProvider(config.ai_api_key, config.ai_base_url, config.ai_model, config.timeout_seconds)


def build_runtime(args: argparse.Namespace, config: AppConfig) -> tuple[ProjectStore, StoryCore]:
    """Create runtime objects inside handled CLI setup so setup errors are readable."""
    provider = select_provider(args, config)
    store = ProjectStore(config.projects_dir)
    core = StoryCore(provider, store)
    return store, core


def request_from_args(args: argparse.Namespace) -> dict:
    return {
        "project_name": args.project_name,
        "story_title": args.story_title,
        "story_topic": args.story_topic,
        "language": args.language,
        "target_duration": args.target_duration,
        "genre": args.genre,
        "visual_style": args.visual_style,
        "number_of_scenes": args.number_of_scenes,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config: AppConfig | None = None
    try:
        config = AppConfig.from_env()
        if args.show_machine_key:
            from app.core.machine import get_machine_key
            print(get_machine_key())
            return 0
        if config.require_machine_key:
            if not config.machine_key:
                raise ConfigError("V01_MACHINE_KEY is required when V01_REQUIRE_MACHINE_KEY is enabled.")
            if not verify_machine_key(config.machine_key):
                raise ConfigError("Machine key does not match this computer.")
        store, core = build_runtime(args, config)
        request = request_from_args(args)
        if args.retry_scene:
            if not args.project_dir:
                raise ValidationError("--project-dir is required when --retry-scene is used")
            scene = core.retry_scene(Path(args.project_dir), request, args.retry_scene)
            print(f"Retried {scene['id']} successfully.")
        else:
            project_path = store.create_project(request)
            core.generate_project_story(project_path, request)
            print(f"Project created: {project_path}")
        return 0
    except (ConfigError, MachineKeyError, ProviderError, StorageError, ValidationError, OSError) as exc:
        if config and config.debug:
            raise
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
