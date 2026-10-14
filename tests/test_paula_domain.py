"""Check Paula's domain-specific front door and independently addressed movie engines."""
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.targets.append(dict(attrs).get('href',''))

def test_portal_only_links_our_two_nodes_and_direct_flow():
    html=(ROOT/'deploy/portal/index.html').read_text(encoding='utf8')
    p=Links();p.feed(html)
    assert p.targets==['https://ph-home.abundent.org/',
                      'https://ph-aws.abundent.org/',
                      'https://www.flowmusic.app/']
    assert '<form' not in html.lower()
    assert '<script' not in html.lower()
    assert 'automatic' in html.lower()
    assert 'private' in html.lower()

def test_node_configuration_never_reuses_one_public_hostname():
    conf=(ROOT/'.env.paula.example').read_text()
    assert 'PAULA_HOME_URL=https://ph-home.abundent.org' in conf
    assert 'PAULA_AWS_URL=https://ph-aws.abundent.org' in conf
    assert 'PAULA_CF_AUD=PASTE_APPLICATION_AUDIENCE_TAG' in conf
    assert 'PAULA_ALLOWED_EMAILS=paula@example.com' in conf
    assert 'PAULA_AUTH_MODE=cloudflare' in conf

def test_aws_bootstrap_sources_pinned_project_branch():
    y=(ROOT/'deploy/aws/paula-ec2.yaml').read_text()
    assert '--branch feature/paula-domain-017-ph-abundent' in y
    assert 'AssociatePublicIpAddress: true' in y
    assert 'Encrypted: true' in y
    assert 'AmazonSSMManagedInstanceCore' in y
    assert 'SecurityGroupIngress' not in y

def test_portal_headers_suppress_embed_and_outbound_fetch():
    head=(ROOT/'deploy/portal/_headers').read_text()
    assert "default-src 'none'" in head
    assert "frame-ancestors 'none'" in head
    assert 'no-store' in head
