"""Separate Home/AWS UI and fail-closed server boundary; no cloud provider required."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from paula_cloud.auth import AuthConfig
from paula_cloud.server import Settings,create_app


def test_node_location_is_private_and_explicit():
    with TemporaryDirectory() as d:
        c=TestClient(create_app(Settings(Path(d),AuthConfig('local'),node_label='Home studio',
                   home_url='https://paula-home.example.com',aws_url='https://paula-aws.example.com')))
        assert c.get('/nodes').status_code==200
        j=c.get('/api/node').json()
        assert j['label']=='Home studio' and j['automatic_failover'] is False
        assert j['shared_projects'] is False and j['storage']=='node-local'
        assert j['home_url']=='https://paula-home.example.com'
        assert 'Choose a studio' in c.get('/').text
        assert 'switch between home' in c.get('/studio/').text.lower()

def test_invalid_unsafe_host_link_is_discarded():
    with TemporaryDirectory() as d:
        c=TestClient(create_app(Settings(Path(d),AuthConfig('local'),node_label='AWS',
                   home_url='javascript:alert(1)',aws_url='https://evil@example.com')))
        j=c.get('/api/node').json()
        assert j['home_url']=='' and j['aws_url']==''

def test_access_auth_fail_closed_for_nodes():
    with TemporaryDirectory() as d:
        c=TestClient(create_app(Settings(Path(d),AuthConfig('cloudflare'))))
        assert c.get('/nodes').status_code==503
        assert c.get('/api/node').status_code==503

def test_independent_node_receipt_secret_and_storage():
    with TemporaryDirectory() as d:
        a=Path(d)/'home';b=Path(d)/'aws'
        create_app(Settings(a,AuthConfig('local')))
        create_app(Settings(b,AuthConfig('local')))
        assert a.joinpath('receipt-secret.key').read_bytes()!=b.joinpath('receipt-secret.key').read_bytes()
        assert a.joinpath('studio.sqlite3').is_file()
        assert b.joinpath('studio.sqlite3').is_file()
