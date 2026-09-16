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
    before = evaluate('window.__oraculo.getState()')
    time.sleep(1)
    after = evaluate('window.__oraculo.getState()')
    assert after['webgl'] and not after['error'] and after['frames'] > before['frames'], after
    pixels = evaluate("(()=>{const c=document.querySelector('#stage canvas'),g=c.getContext('webgl2')||c.getContext('webgl');const p=new Uint8Array(4);g.readPixels(c.width>>1,c.height>>1,1,1,g.RGBA,g.UNSIGNED_BYTE,p);return {width:c.width,height:c.height,center:Array.from(p)}})()")
    assert pixels['width'] > 0 and pixels['height'] > 0 and pixels['center'][3] > 0, pixels
    png = base64.b64decode(call('Page.captureScreenshot', {'format': 'png'})['data'])
    assert png.startswith(b'\x89PNG') and len(png) > 10000
    (OUT / (run + '.png')).write_bytes(png)
    evaluate('document.title')
    assert not errors, errors
    report.update({'pass': True, 'state': after, 'canvas': pixels, 'consoleErrors': errors, 'screenshotBytes': len(png), 'screenshot': str(OUT / (run + '.png'))})
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
