"""Briefly: a Python/Flask implementation of the same client portal as the Next.js demo.
Auth and row-level security live in Supabase. No privileged provider keys are used.
"""
import json, os, re, uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from flask import Flask, request, jsonify, send_from_directory, g
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 12000

def origin(): return os.environ.get('APP_ORIGIN', 'http://localhost:3000').rstrip('/')
def cookie_name(kind): return ('__Host-' if origin().startswith('https:') else '') + 'briefly-' + kind
class Failure(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

def remote(url, method='GET', body=None, headers=None):
    req = Request(url, data=json.dumps(body).encode() if body is not None else None, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=20) as r: return r.status, json.loads(r.read() or b'null')
    except HTTPError as e:
        try: data = json.loads(e.read())
        except ValueError: data = None
        return e.code, data

def sb(path, token=None, method='GET', body=None, prefer=None):
    key = os.environ['SUPABASE_ANON_KEY']
    headers = {'apikey': key, 'Authorization': 'Bearer ' + (token or key), 'Content-Type': 'application/json'}
    if prefer: headers['Prefer'] = prefer
    return remote(os.environ['SUPABASE_URL'] + path, method, body, headers)

def reply(data, status=200):
    r = jsonify(data); r.status_code = status; r.headers['Cache-Control'] = 'no-store'; r.headers['X-Content-Type-Options'] = 'nosniff'
    options = dict(httponly=True, secure=origin().startswith('https:'), samesite='Lax', path='/')
    if getattr(g, 'session', None):
        r.set_cookie(cookie_name('access'), g.session['access_token'], max_age=3600, **options)
        if g.session.get('refresh_token'): r.set_cookie(cookie_name('refresh'), g.session['refresh_token'], max_age=604800, **options)
    if getattr(g, 'clear', False):
        for k in ['access', 'refresh']: r.set_cookie(cookie_name(k), '', max_age=0, **options)
    return r

@app.route('/api/<path:path>', methods=['GET','POST','PUT','PATCH','DELETE'])
def api(path):
    from urllib.parse import quote
    g.session, g.clear = None, False
    try:
        method = request.method
        if path == 'health' and method == 'GET': return reply({'ok': True, 'stack': 'python'})
        if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_ANON_KEY'): raise Failure(503, 'Connect this app to Supabase first. See Make it yours for setup instructions.')
        body = {}
        if method != 'GET':
            if request.headers.get('Origin') != origin(): raise Failure(403, 'Request origin rejected.')
            if not request.is_json: raise Failure(415, 'Send JSON.')
            body = request.get_json(silent=True)
            if not isinstance(body, dict): raise Failure(400, 'Invalid JSON.')
        def email():
            if not isinstance(body.get('email'), str) or not re.fullmatch(r'\S+@\S+\.\S+', body['email']) or len(body['email']) > 254: raise Failure(400, 'Enter a valid email address.')
        def password():
            if not isinstance(body.get('password'), str) or not 10 <= len(body['password']) <= 128: raise Failure(400, 'Use a password of 10–128 characters.')
        if path in ['login','signup'] and method == 'POST':
            email(); password()
            status, data = sb('/auth/v1/token?grant_type=password' if path == 'login' else '/auth/v1/signup?redirect_to=' + quote(origin() + '/callback', safe=''), method='POST', body={'email':body['email'],'password':body['password']})
            if status >= 400: raise Failure(429 if status == 429 else 400, 'Email or password not accepted.' if path == 'login' else (data or {}).get('msg', 'Unable to create account.'))
            if not data.get('access_token'): return reply({'pendingConfirmation': True})
            g.session = data; return reply({'user': {'id':data['user']['id'],'email':data['user']['email']}})
        if path == 'recover' and method == 'POST':
            email(); status, data = sb('/auth/v1/recover?redirect_to=' + quote(origin() + '/reset', safe=''), method='POST', body={'email':body['email']})
            if status == 429: raise Failure(429, 'Please wait before requesting another reset link.')
            if status >= 500: raise Failure(503, 'Password recovery is temporarily unavailable. Please try again.')
            return reply({'ok':True})
        if path == 'callback' and method == 'POST':
            if not isinstance(body.get('access_token'), str) or not isinstance(body.get('refresh_token'), str): raise Failure(400, 'Invalid confirmation link.')
            status, data = sb('/auth/v1/user', token=body['access_token'])
            if status >= 400: raise Failure(401, 'This link expired. Request a new one.')
            g.session = body; return reply({'ok':True})
        token = request.cookies.get(cookie_name('access')); status, user = sb('/auth/v1/user', token=token) if token else (401, None)
        if status >= 400 and request.cookies.get(cookie_name('refresh')):
            rs, data = sb('/auth/v1/token?grant_type=refresh_token', method='POST', body={'refresh_token':request.cookies[cookie_name('refresh')]})
            if rs < 400:
                g.session = data; token = data['access_token']; status, user = sb('/auth/v1/user', token=token)
        if path == 'logout' and method == 'POST':
            if status < 400: sb('/auth/v1/logout', token=token, method='POST')
            g.clear = True; return reply({'ok':True})
        if status >= 400:
            g.clear = True
            if path == 'session' and method == 'GET': return reply({'user':None})
            raise Failure(401, 'Sign in to continue.')
        if path == 'session' and method == 'GET': return reply({'user':{'id':user['id'],'email':user['email']}})
        if path == 'password' and method == 'PUT':
            password(); status, data = sb('/auth/v1/user', token=token, method='PUT', body={'password':body['password']})
            if status >= 400: raise Failure(400, (data or {}).get('msg', 'Unable to change password.'))
            return reply({'ok':True})
        if path == 'requests' and method == 'GET':
            status, data = sb('/rest/v1/client_requests?select=*&order=created_at.desc&limit=100', token=token)
            if status >= 400: raise Failure(503, 'The requests table is not ready. Ask your agent to apply schema.sql.')
            return reply(data)
        if path == 'requests' and method == 'POST':
            if not isinstance(body.get('title'),str) or not body['title'].strip() or len(body['title'])>120 or not isinstance(body.get('description'),str) or not body['description'].strip() or len(body['description'])>3000 or body.get('category') not in ['Website','Brand','Content','Other']: raise Failure(400,'Add a title, details and category.')
            status, data = sb('/rest/v1/client_requests', token=token, method='POST', body={'user_id':user['id'],'title':body['title'].strip(),'description':body['description'].strip(),'category':body['category']}, prefer='return=representation')
            if status >= 400: raise Failure(400,'Unable to save this request.')
            return reply(data[0],201)
        match = re.fullmatch(r'requests/([0-9a-f-]{36})',path)
        if match and method in ['PATCH','DELETE']:
            if method == 'PATCH' and body.get('status') not in ['new','in_progress','done']: raise Failure(400,'Invalid status.')
            status, data = sb('/rest/v1/client_requests?id=eq.'+match[1],token=token,method=method,body={'status':body['status']} if method=='PATCH' else None,prefer='return=representation')
            if status >= 400: raise Failure(400,'Unable to update this request.')
            if not data: raise Failure(404,'Request not found.')
            return reply({'ok':True})
        if path == 'email/test' and method == 'POST':
            if not os.environ.get('LB_RUNTIME_TOKEN') or not os.environ.get('LB_RUNTIME_URL'): raise Failure(503,'Ask your agent to enable email and configure Launchbase runtime access.')
            status,data=remote(os.environ['LB_RUNTIME_URL']+'/email/test',method='POST',body={'userAccessToken':token,'idempotencyKey':str(uuid.uuid4())},headers={'Authorization':'Bearer '+os.environ['LB_RUNTIME_TOKEN'],'Content-Type':'application/json','Accept':'application/json'})
            if status>=400 or data.get('status') not in ['sent','delivered']: raise Failure(429 if status==429 else 503, (data.get('error') or {}).get('message','Email could not be sent. Check the app’s email service in Launchbase.'))
            return reply({'ok':True})
        raise Failure(404,'Not found.')
    except Failure as e: return reply({'error':e.message},e.status)
    except Exception: return reply({'error':'Service temporarily unavailable. Please try again.'},503)

@app.route('/')
@app.route('/login')
@app.route('/register')
@app.route('/forgot')
@app.route('/reset')
@app.route('/callback')
@app.route('/app')
@app.route('/guide')
def page(): return send_from_directory('public','index.html')

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Frame-Options']='DENY'
    if request.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    return response

if __name__ == '__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT','3000')),debug=False)
