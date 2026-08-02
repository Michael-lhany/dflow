from dflow.config import get_flow_options


def test_cli_options_append_to_configured_options():
    flow_config = {
        "lint": {
            "options": ["--lint-only"],
            "_cli_options": ["-Wall"],
        }
    }

    assert get_flow_options(flow_config, "lint") == ["--lint-only", "-Wall"]
