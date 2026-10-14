"""The Cloudflare Pages Kling planner is a working, browser-local static application."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAKE = ROOT / "deploy" / "portal" / "make"


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.scripts = []
        self.forms = 0
        self.inline_handlers = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            self.links.append(a.get("href", ""))
        if tag == "script":
            self.scripts.append(a)
        if tag == "form":
            self.forms += 1
        self.inline_handlers.extend(k for k, _ in attrs if k.startswith("on"))


def test_kling_planner_has_no_network_or_inline_script():
    html = (MAKE / "index.html").read_text()
    js = (MAKE / "app.js").read_text()
    scan = Scan()
    scan.feed(html)
    assert len(scan.ids) == len(set(scan.ids))
    assert {"title", "story", "characters", "mood", "ratio", "shots", "notice",
            "add", "save", "copyAll", "import", "importFile", "exportPocket",
            "total", "count"}.issubset(scan.ids)
    assert scan.forms == 0
    assert scan.inline_handlers == []
    assert len(scan.scripts) == 1 and scan.scripts[0].get("src") == "/make/app.js"
    assert scan.scripts[0].get("defer") is None
    assert "https://kling.ai/" in scan.links
    assert "XMLHttpRequest" not in js
    assert "fetch(" not in js
    assert "WebSocket(" not in js
    assert "sendBeacon" not in js
    assert "localStorage" in js and "normalized(" in js
    assert "shot-kit backup" in html
    headers = (ROOT / "deploy" / "portal" / "_headers").read_text()
    assert "script-src 'self'" in headers
    assert "connect-src 'none'" in headers
    assert "default-src 'none'" in headers
    assert "frame-ancestors 'none'" in headers


@pytest.mark.skipif(not shutil.which("node"), reason="Node needed for JavaScript unit smoke")
def test_kling_shot_planner_roundtrip_and_prompt_safety():
    """Execute the real pure JS core under a locked-down Node VM without a DOM/network."""
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const code = fs.readFileSync('deploy/portal/make/app.js','utf8');
new vm.Script(code); // Compile the ENTIRE shipping JavaScript
const prefix = code.split('function init(){')[0];
assert.ok(prefix.length > 2000,'Script refactored; update this test rather than silently skipping');
const ctx = vm.createContext({crypto:require('node:crypto').webcrypto});
const run = code => vm.runInContext(code,ctx);
run(prefix);
run('kit=fresh()');
run("kit.title='Autumn kindness'; kit.story='A hopeful meeting'; kit.characters='Same people, same hats';");
run("kit.shots[0].action='An old bicycle returns';");
let prompt=run('promptFor(kit.shots[0],0)');
assert.ok(prompt.includes('Autumn kindness'));
assert.ok(prompt.includes('A hopeful meeting'));
assert.ok(prompt.includes('Same people'));
let exportStory=run('pocketProject()');
assert.equal(exportStory.format,'vidmage/paula-pocket-project/v1');
assert.equal(exportStory.receipts.length,0); // approval must happen on the private server
assert.equal(exportStory.scenes.length,1);
assert.equal(exportStory.scenes[0].action,'An old bicycle returns');
assert.equal(exportStory.duration,20);
assert.ok(/^pocket-[a-f0-9]{24}$/.test(exportStory.projectId));
let kit=run('normalized(kit)');
assert.equal(kit.shots.length,1);
assert.throws(()=>run("normalized({format:FORMAT,shots:[]})"));
assert.throws(()=>run("normalized({format:FORMAT,shots:Array.from({length:13},()=>({name:'x'}))})"));
assert.equal(run("clipLength(999)"),30);
assert.equal(run("safe('<img src=x onerror=alert(1)>')"),'&lt;img src=x onerror=alert(1)&gt;');
run('kit.shots[0].seconds=30');
run('kit.shots.push(shot()); kit.shots[1].seconds=30');
assert.equal(run('getDuration()'),60);
console.log('browser-only core and portable storyboard verified');
"""
    proc = subprocess.run(
        ["node", "-"], input=script, cwd=ROOT, text=True,
        capture_output=True, timeout=20, check=False
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_portal_has_working_first_door_and_truthful_offline_rooms():
    html = (ROOT / "deploy" / "portal" / "index.html").read_text()
    assert 'href="/make/"' in html
    assert html.index('href="/make/"') < html.index('href="https://ph-home.abundent.org/"')
    assert "not connected yet" in html
    assert "AWS machine would incur charges" in html
