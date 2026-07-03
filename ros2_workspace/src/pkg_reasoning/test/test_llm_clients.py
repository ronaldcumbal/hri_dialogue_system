import pytest

from pkg_reasoning.llm_clients import TestClient, create_llm_client


def test_create_llm_client_test_backend():
    client = create_llm_client('test')
    assert isinstance(client, TestClient)


def test_test_client_generates_a_string_response():
    client = TestClient()
    response = client.generate('hello')
    assert isinstance(response, str)
    assert response != ''


def test_create_llm_client_rejects_unknown_backend():
    with pytest.raises(ValueError):
        create_llm_client('not_a_real_backend')
