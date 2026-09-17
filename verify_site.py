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
    check('WebGL ready',"__oraculo.getState().webgl && __oraculo.getState().frames>0")
    check('Six release entries',"__site.releases===6 && document.querySelectorAll('.release-card').length===6")
    check('No unsolicited media',"__site.getState().externalMedia===0")
    shot('desktop-hero')
    evaluate("document.getElementById('motion').click()")
    check('Pause button',"__oraculo.getState().paused")
    f=evaluate('__oraculo.getState().frames');time.sleep(.8)
    check('Paused rendering stops',f"__oraculo.getState().frames==={f}")
    evaluate("document.getElementById('rotate-right').click()")
    check('Manual rotation redraw',f"__oraculo.getState().frames>{f}")
    evaluate("document.getElementById('catalog-search').value='metafisica';document.getElementById('catalog-search').dispatchEvent(new Event('input'))")
    check('Accent-insensitive search',"__site.getState().visible===1")
    evaluate("document.getElementById('catalog-search').value='zzzzzz';document.getElementById('catalog-search').dispatchEvent(new Event('input'))")
    check('Empty search state',"__site.getState().visible===0 && !document.getElementById('empty').hidden")
    evaluate("document.getElementById('catalog-search').value='';document.getElementById('catalog-search').dispatchEvent(new Event('input'))")
    check('Reset search',"__site.getState().visible===6")
    evaluate("document.querySelector('[data-release=\"1\"]').click()")
    check('Release dialog content',"document.getElementById('release-modal').open && document.getElementById('modal-artist').textContent==='ESTADO DE BIENESTAR'")
    shot('release-dialog')
    call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Escape','code':'Escape','windowsVirtualKeyCode':27})
    call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Escape','code':'Escape','windowsVirtualKeyCode':27})
    time.sleep(.2)
    check('Escape closes dialog',"!document.getElementById('release-modal').open")
    evaluate("document.getElementById('credits-open').click()")
    check('Credits dialog',"document.getElementById('credits-modal').open")
    evaluate("document.getElementById('credits-modal').close()")
    for width,height in [(1440,1000),(1024,900),(768,1000),(375,812)]:
        call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
        evaluate("document.documentElement.style.scrollBehavior='auto';scrollTo(0,0)")
        time.sleep(.6)
        print('LAYOUT',width,evaluate("Array.from(document.querySelectorAll('body *')).filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!e.closest('dialog')}).map(e=>({tag:e.tagName,cls:e.className,right:Math.round(e.getBoundingClientRect().right)})).slice(0,20)"))
        check(f'No horizontal overflow {width}',"document.documentElement.scrollWidth<=innerWidth+1")
        for target in ['releases','about','journal','artists','ombra']:
            evaluate(f"document.getElementById('{target}').scrollIntoView()")
            time.sleep(.3)
        evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('seen'));scrollTo(0,0)")
        time.sleep(.5)
        check(f'Images loaded {width}',"Array.from(document.images).filter(i=>!i.closest('dialog')).every(i=>i.complete&&i.naturalWidth>0)")
        if width in [1440,375]:shot(f'full-{width}',True);shot(f'hero-{width}')
    evaluate("document.querySelector('.menu-toggle').click()")
    check('Mobile menu opens',"__site.getState().menuOpen")
    evaluate("document.querySelector('#main-nav a').click()")
    check('Mobile navigation closes menu',"!__site.getState().menuOpen")
    call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'reduce'}]})
    time.sleep(.4)
    check('Reduced-motion respected',"__oraculo.getState().paused")
    call('Page.navigate',{'url':URL+'?fallback'})
    time.sleep(3)
    check('Static fallback',"document.body.classList.contains('no-webgl')&&document.querySelector('.fallback').getBoundingClientRect().width>0")
    shot('mobile-fallback')
    call('Page.navigate',{'url':ROOT.joinpath('index.html').as_uri()})
    time.sleep(4)
    check('Double-click file support',"location.protocol==='file:'&&__site.releases===6&&__oraculo.getState().webgl")
    check('Local assets loaded',"Array.from(document.images).filter(i=>!i.loading&&!i.closest('dialog')).every(i=>i.naturalWidth>0)")
    assert not errors,errors
    report.update({'pass':True,'checks':checks,'consoleErrors':errors})

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
