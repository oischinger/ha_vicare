"""Test for ViCare."""
from unittest.mock import AsyncMock, Mock, patch


class MockViCareClient(Mock):
    """An async context manager mock for Vicare."""


def create_mock_client() -> Mock:
    """Create a mock ViCare client."""
    mock_client = MockViCareClient()
    # pylint: disable=attribute-defined-outside-init
    mock_client.async_client_connect = AsyncMock(return_value=True)
    mock_client.async_client_disconnect = AsyncMock(return_value=True)
    return mock_client
