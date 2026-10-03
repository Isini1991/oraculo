import json, time, subprocess, urllib.request, base64, pathlib
import websocket
ROOT=pathlib.Path('C:/Users/Esi/oraculo-site')
OUT=ROOT/'verification';OUT.mkdir(exist_ok=True)
chrome='C:/Program Files/Google/Chrome/Application/chrome.exe'
proc=subprocess.Popen([chrome,'--headless=new','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9348','--remote-allow-origins=*','--user-data-dir=C:/tmp/oraculo-cdp','--no-first-run','--hide-scrollbars','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    tabs=None
    for _ in range(40):
        try:
            tabs=json.load(urllib.request.urlopen('http://127.0.0.1:9348/json',timeout=1));break
        except Exception:time.sleep(.25)
    ws=websocket.create_connection(tabs[0]['webSocketDebuggerUrl'],timeout=30);seq=0;errors=[]
    def call(method,params=None):
        global seq
        seq+=1;i=seq;ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
        while True:
            msg=json.loads(ws.recv())
            if msg.get('method')=='Runtime.exceptionThrown':errors.append(msg['params'])
            if msg.get('id')==i:return msg.get('result',{})
    def evaluate(expr):return call('Runtime.evaluate',{'expression':expr,'returnByValue':True}).get('result',{}).get('value')
    call('Page.enable');call('Runtime.enable');call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
    call('Page.navigate',{'url':'http://127.0.0.1:8768/' });time.sleep(12)
    print('PAGE',evaluate('({url:location.href,ready:document.readyState,title:document.title,body:document.body?.innerText?.slice(0,100)})'))
    print('ERRORS BEFORE SHOT',errors)
    state=evaluate('window.__oraculo?.getState()');print('STATE',state)
    shot=call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,'clip':{'x':0,'y':0,'width':1440,'height':evaluate('document.documentElement.scrollHeight'),'scale':1}});(OUT/'hero-initial.png').write_bytes(base64.b64decode(shot['data']))
    print('ERRORS',errors);print('SCREENSHOT',str(OUT/'hero-initial.png'))
    (OUT/'initial.json').write_text(json.dumps({'state':state,'errors':errors},indent=2))
    ws.close()
finally:
    proc.terminate()
