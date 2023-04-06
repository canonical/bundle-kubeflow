import inspect


def validate_response_status_code(response, expected_codes: list, error_message: str = ""):
    """Validates the status code of a response, raising a ValueError with message"""
    if error_message:
        error_message += "  "
    if response.status_code not in expected_codes:
        raise ValueError(
            f"{error_message}"
            f"Got response {response.status_code}, expected one of {expected_codes}"
        )


def get_pipeline_params(func):
    return {name: value.default for name, value in inspect.signature(func).parameters.items()}
