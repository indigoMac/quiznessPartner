from pathlib import Path
from unittest.mock import patch

from env_loader import BACKEND_DIR, ROOT_DIR, load_app_env


def test_loads_backend_env_then_repo_root_env():
    with patch("env_loader.load_dotenv") as mock_load:
        load_app_env()

    assert mock_load.call_args_list[0].args[0] == BACKEND_DIR / ".env"
    assert mock_load.call_args_list[1].args[0] == ROOT_DIR / ".env"
    assert BACKEND_DIR.name == "backend"
    assert ROOT_DIR == Path(BACKEND_DIR).parent
