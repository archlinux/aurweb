from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from aurweb.asgi import app

client = TestClient(app)


def test_homepage():
    with client as request:
        response = request.get("/")
    assert response.status_code == int(HTTPStatus.OK)


@patch('aurweb.util.get_ssh_fingerprints')
def test_homepage_ssh_fingerprints(get_ssh_fingerprints_mock):
    fingerprints = {'Ed25519': "SHA256:RFzBCUItH9LZS0cKB5UE6ceAYhBD5C8GeOBip8Z11+4"}
    get_ssh_fingerprints_mock.return_value = fingerprints

    with client as request:
        response = request.get("/")

    assert list(fingerprints.values())[0] in response.content.decode()
    assert 'The following SSH fingerprints are used for the AUR' in response.content.decode()


@patch('aurweb.util.get_ssh_fingerprints')
def test_homepage_no_ssh_fingerprints(get_ssh_fingerprints_mock):
    get_ssh_fingerprints_mock.return_value = {}

    with client as request:
        response = request.get("/")

    assert 'The following SSH fingerprints are used for the AUR' not in response.content.decode()
