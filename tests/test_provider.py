import base64
import io
import json
import socket
from pathlib import Path
from urllib import error

import pytest
from PIL import Image
from poster_agent.provider import Gateway,ProviderFailure,multipart,public_https,http
from poster_agent.core import PosterError

CONFIG={r:{"base_url":"https://example.com/v1","model":"fixture","api_key":"fixture-secret"} for r in ("image","vision")}


def png():
    b=io.BytesIO();Image.new("RGB",(1024,1024)).save(b,"PNG");return b.getvalue()


def test_edit_multipart_contains_actual_reference(tmp_path):
    p=tmp_path/"reference.png";p.write_bytes(png());seen=[]
    def transport(url,body=None,headers=None):
        seen.append((url,body,headers))
        return json.dumps({"data":[{"b64_json":base64.b64encode(png()).decode()}]}).encode(),{}
    result,_=Gateway(CONFIG,transport).image("preserve",(1024,1024),[p])
    assert seen[0][0].endswith("/images/edits")
    assert b'name="image[]"' in seen[0][1] and b"PNG" in seen[0][1]
    assert "multipart/form-data" in seen[0][2]["Content-Type"]
    assert b"input_fidelity" not in seen[0][1]


def test_url_result_download_has_no_authorization():
    seen=[]
    def transport(url,body=None,headers=None):
        seen.append((url,headers))
        if url.endswith("/generations"):return b'{"data":[{"url":"https://cdn.example.com/file.png"}]}',{}
        return png(),{}
    Gateway(CONFIG,transport).image("x",(1024,1024),[])
    assert seen[1][1] is None


def test_vision_sends_inline_image_and_validates_json(tmp_path):
    p=tmp_path/"photo.png";p.write_bytes(png());seen=[]
    def transport(url,body=None,headers=None):
        seen.append(json.loads(body))
        return b'{"choices":[{"message":{"content":"{\\"answer\\":1}"}}]}',{}
    data,_=Gateway(CONFIG,transport).vision("read",[p])
    assert data=={"answer":1}
    assert seen[0]["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_unreadable_image_is_unknown():
    g=Gateway(CONFIG,lambda *a,**kw:(b'{"data":[{"b64_json":"garbage"}]}',{}))
    with pytest.raises(ProviderFailure) as e:g.image("x",(1024,1024),[])
    assert e.value.uncertain


def test_provider_error_never_echoes_secrets():
    g=Gateway(CONFIG,lambda *a,**kw:(b'{"error":"fixture-secret private prompt"}',{}))
    with pytest.raises(ProviderFailure) as e:g.vision("x",[])
    assert "fixture-secret" not in str(e.value)


@pytest.mark.parametrize("ip",["127.0.0.1","10.1.1.1","169.254.169.254","::1"])
def test_private_network_rejected(monkeypatch,ip):
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,"",(ip,443))])
    with pytest.raises(PosterError):public_https("https://example.com/a")


def test_redirects_blocked_and_dns_is_pinned(monkeypatch):
    import poster_agent.provider as module
    seen=[]
    monkeypatch.setattr(module,"public_https",lambda u,*a:["8.8.8.8"])
    monkeypatch.setattr(socket,"create_connection",lambda address,*a:seen.append(address))
    class Connection:
        def __init__(self,host,port,timeout):assert host=="example.com"
        def request(self,*args,**kwargs):self._create_connection(("example.com",443),180)
        def getresponse(self):return type("Response",(),{"status":302})()
        def close(self):pass
    monkeypatch.setattr(module.http_client,"HTTPSConnection",Connection)
    with pytest.raises(ProviderFailure,match="HTTP_302"):http("https://example.com/test",headers={"Authorization":"Bearer fixture"})
    assert seen==[("8.8.8.8",443)]


def test_fake_dns_is_opt_in_and_host_scoped(monkeypatch):
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,"",("198.18.0.20",443))])
    with pytest.raises(PosterError):public_https("https://example.com/a")
    assert public_https("https://example.com/a",{"example.com"})==["198.18.0.20"]
    with pytest.raises(PosterError):public_https("https://untrusted.example/a",{"example.com"})


def test_fake_dns_never_allows_loopback(monkeypatch):
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))])
    with pytest.raises(PosterError):public_https("https://example.com/a",{"example.com"})
