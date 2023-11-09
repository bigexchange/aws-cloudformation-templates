import pytest
from unittest.mock import Mock, patch
import requests
from ecs_scaler_lambda import get_token, main

# Mock requests
@patch("requests.get")
def test_get_token(mock_requests_get):
    # Replace with your test data
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"systemToken": "mock_system_token"}
    mock_requests_get.return_value = mock_response

    refresh_token = "mock_refresh_token"
    host_name = "mock_host_name"

    system_token = get_token(refresh_token, host_name)

    assert system_token == "mock_system_token"
    mock_requests_get.assert_called_once_with(
        f"https://{host_name}/api/v1/refresh-access-token",
        headers={"Authorization": {refresh_token}, "Content-Type": "application/json"},
    )

@patch("ecs_scaler_lambda.get_token")
@patch("ecs_scaler_lambda.scale_ecs_task_definition")
def test_main(mock_scale_ecs_task_definition, mock_get_token):
    # Replace with your test data
    refresh_token = "mock_refresh_token"
    host_name = "mock_host_name"
    cluster_name = "mock_cluster_name"
    service_name = "mock_service_name"
    task_definition = "mock_task_definition"
    desired_count = 2
    region_name = "mock_region_name"

    mock_get_token.return_value = "mock_system_token"
    mock_scale_ecs_task_definition.return_value = "Success"

    result = main(
        refresh_token,
        host_name,
        cluster_name,
        service_name,
        task_definition,
        desired_count,
        region_name,
    )

    assert result == "Success"
    mock_get_token.assert_called_once_with(refresh_token, host_name)
    mock_scale_ecs_task_definition.assert_called_once_with(
        cluster_name, service_name, task_definition, desired_count
    )

if __name__ == "__main__":
    pytest.main()
