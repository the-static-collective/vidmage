"""Enforce Cloudflare Access signed tokens at origin, no trusted header shortcuts."""
import os
from dataclasses import dataclass
from urllib.parse import urlparse
import jwt
from fastapi import HTTPException, Request

@dataclass(frozen=True)
class AuthConfig:
    mode:str='cloudflare'
    team_domain:str=''
    audience:str=''
    allowed_emails:tuple[str,...]=()

def from_env():
    mode=os.environ.get('PAULA_AUTH_MODE','cloudflare').strip().lower()
    team=os.environ.get('PAULA_CF_TEAM_DOMAIN','').strip().rstrip('/')
    aud=os.environ.get('PAULA_CF_AUD','').strip()
    emails=tuple(x.lower().strip() for x in os.environ.get('PAULA_ALLOWED_EMAILS','').split(',') if x.strip())
    return AuthConfig(mode,team,aud,emails)

def identity(request:Request,config:AuthConfig)->str:
    if config.mode=='local':
        # Never use this mode on any publicly reachable listening interface.
        return 'local-operator'
    if config.mode!='cloudflare' or not config.team_domain or not config.audience or not config.allowed_emails:
        raise HTTPException(503,'Cloudflare Access not configured')
    parsed=urlparse(config.team_domain)
    if (parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.cloudflareaccess.com')
        or parsed.path not in ('','/') or parsed.query or parsed.fragment):
        raise HTTPException(503,'Invalid Cloudflare Access team domain')
    token=request.headers.get('Cf-Access-Jwt-Assertion')
    if not token:raise HTTPException(401,'Cloudflare Access login required')
    try:
        key=jwt.PyJWKClient(config.team_domain+'/cdn-cgi/access/certs',cache_jwk_set=True,lifespan=3600).get_signing_key_from_jwt(token)
        data=jwt.decode(token,key.key,algorithms=['RS256'],audience=config.audience,
                        issuer=config.team_domain,options={'require':['exp','iat','iss','aud']})
    except Exception:
        raise HTTPException(401,'Cloudflare Access token invalid') from None
    user=str(data.get('email','')).strip().lower()
    if not user or user not in config.allowed_emails:
        raise HTTPException(403,'User not allowed')
    return user
