import base64
import json
import pathlib
import socket
import subprocess
import tempfile
import time
import urllib.request
import websocket

ROOT = pathlib.Path('C:/Users/Esi/oraculo-site')
OUT = ROOT / 'verification'
OUT.mkdir(exist_ok=True)
URL = 'http://127.0.0.1:8768/'
assert urllib.request.urlopen(URL, timeout=10).status == 200
profile = pathlib.Path(tempfile.mkdtemp(prefix='oraculo-clean-', dir='C:/tmp'))
run = profile.name
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
proc = subprocess.Popen([
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    '--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    '--remote-debugging-port=' + str(port), '--remote-allow-origins=*',
    '--user-data-dir=' + str(profile), '--no-first-run', '--hide-scrollbars',
    '--disable-background-networking', 'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ws = None
errors = []
seq = 0
report = {'run': run, 'url': URL, 'pass': False}
checks=[]
try:
    deadline = time.monotonic() + 25
    while True:
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=1))
            page = next(t for t in tabs if t['type'] == 'page')
            break
        except Exception:
            if time.monotonic() > deadline:
                raise TimeoutError('Fresh Chrome did not become ready')
            time.sleep(.25)
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=45)
    def call(method, params=None):
        global seq
        seq += 1
        ident = seq
        ws.send(json.dumps({'id': ident, 'method': method, 'params': params or {}}))
        while True:
            event = json.loads(ws.recv())
            if event.get('method') == 'Runtime.exceptionThrown':
                errors.append(event['params'])
            if event.get('method') == 'Runtime.consoleAPICalled' and event['params']['type'] == 'error':
                errors.append(event['params'])
            if event.get('id') == ident:
                if 'error' in event:
                    raise RuntimeError(event['error'])
                return event.get('result', {})
    def evaluate(expression):
        result = call('Runtime.evaluate', {'expression': expression, 'returnByValue': True})
        if 'exceptionDetails' in result:
            raise RuntimeError(result['exceptionDetails'])
        return result.get('result', {}).get('value')
    call('Page.enable')
    call('Runtime.enable')
    call('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': False})
    call('Page.navigate', {'url': URL})
    deadline = time.monotonic() + 50
    while True:
        ready = evaluate("document.readyState==='complete' && !!document.querySelector('#stage canvas') && !!window.__oraculo?.getState().ready")
        if ready:
            break
        if time.monotonic() > deadline:
            raise TimeoutError('Document and WebGL canvas not ready: ' + json.dumps(errors))
        time.sleep(.3)
    call('Runtime.evaluate', {'expression': 'document.fonts.ready', 'awaitPromise': True})
    time.sleep(2)
    def check(name, expression):
        value=evaluate(expression)
        checks.append({'name':name,'pass':bool(value),'value':value})
        if not value: raise AssertionError(name+': '+str(value))
    def shot(name,full=False):
        params={'format':'png'}
        if full:params.update({'captureBeyondViewport':True,'clip':{'x':0,'y':0,'width':evaluate('innerWidth'),'height':evaluate('document.documentElement.scrollHeight'),'scale':1}})
        data=base64.b64decode(call('Page.captureScreenshot',params)['data']);(OUT/(name+'.png')).write_bytes(data)
    check('WebGL ready',"__oraculo.getState().webgl")
    check('Initial orientation identity',"__oraculo.getState().quaternion.every((n,i)=>Math.abs(n-(i===3?1:0))<1e-9)")
    check('Slow selector matches default',"__oraculo.getState().rpm===50/3 && document.querySelector('[data-rpm=\"slow\"]').getAttribute('aria-pressed')==='true'")
    start=evaluate('({s:__oraculo.getState(),t:performance.now()})');time.sleep(2)
    end=evaluate('({s:__oraculo.getState(),t:performance.now()})')
    actual=(start['s']['spin']-end['s']['spin'])/((end['t']-start['t'])/1000)*60/(2*3.141592653589793)
    checks.append({'name':'Measured slow RPM','value':actual,'pass':abs(actual-50/3)<1.5})
    assert abs(actual-50/3)<1.5,actual
    for width,height in [(1440,1000),(375,812)]:
        call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False});time.sleep(.5)
        check(f'Face remains flat {width}',"__oraculo.getState().rotation.slice(0,3).every(n=>n===0)")
        check(f'Centered {width}',"Math.abs((__oraculo.getState().bounds.left+__oraculo.getState().bounds.right)/2-innerWidth/2)<1")
        check(f'Title overlap bounded {width}',"(()=>{const b=__oraculo.getState().bounds,t=document.getElementById('hero-title').getBoundingClientRect();return t.bottom-b.top>5&&t.bottom-b.top<65})()")
        if width==375:check('Controls below record',"document.querySelector('.vinyl-controls').getBoundingClientRect().top>__oraculo.getState().bounds.bottom+8")
        shot(f'slow-flat-{width}')
    assert not errors,errors
    report.update({'pass':True,'checks':checks,'initial':start,'final':end,'consoleErrors':errors})

finally:
    if ws:
        ws.close()
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    (OUT / (run + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
