from pathlib import Path

from app.core.config import Settings, resolve_env_file, resolve_profile


def test_resolve_profile_prefers_env_var():
    env = {"APP_PROFILE": "prod"}
    argv = ["python", "--profile=dev"]

    profile = resolve_profile(argv=argv, env=env)

    assert profile == "prod"


def test_resolve_profile_from_argv():
    env = {}
    argv = ["python", "-m", "app.main", "--profile=dev"]

    profile = resolve_profile(argv=argv, env=env)

    assert profile == "dev"


def test_resolve_profile_default_none():
    env = {}
    argv = ["python", "-m", "app.main"]

    profile = resolve_profile(argv=argv, env=env)

    assert profile is None


def test_resolve_env_file_with_profile():
    base_dir = Path("/tmp/backend")

    assert resolve_env_file(base_dir, "uat") == base_dir / ".env.uat"


def test_resolve_env_file_without_profile():
    base_dir = Path("/tmp/backend")

    assert resolve_env_file(base_dir, None) == base_dir / ".env"


def test_app_port_from_settings():
    settings = Settings(APP_PORT=8012)

    assert settings.APP_PORT == 8012
