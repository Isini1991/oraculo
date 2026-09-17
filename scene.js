(()=>{'use strict';
const host=document.getElementById('stage'),hero=document.getElementById('hero'),motion=document.getElementById('motion');
const media=matchMedia('(prefers-reduced-motion: reduce)');
const state={ready:false,frames:0,webgl:false,error:null,paused:media.matches,visible:true,progress:0,drawCalls:0};
let renderer,scene,camera,disc,raf=0,last=0,tx=0,ty=0,spin=-.18,manual=0;
window.__oraculo={getState:()=>({...state}),force(p=0){state.progress=p;update(0);draw()}};
function syncButton(){motion.textContent=state.paused?'▷ Resume motion':'Ⅱ Pause motion';motion.setAttribute('aria-pressed',String(state.paused))}
syncButton();
function draw(){if(!renderer||!state.webgl)return;renderer.render(scene,camera);state.frames++;state.drawCalls=renderer.info.render.calls}
function update(dt){if(!disc)return;const p=state.progress;spin-=dt*.055;disc.rotation.z=spin+manual;disc.rotation.x+=(.5+ty+p*.7-disc.rotation.x)*Math.min(1,.08+dt*2);disc.rotation.y+=(-.35+tx-p*.35-disc.rotation.y)*Math.min(1,.08+dt*2);disc.position.y=-.82+p*.5}
function tick(now){raf=0;const dt=Math.min((now-last)/1000,.05);last=now;if(!state.paused&&!document.hidden&&state.visible){update(dt);draw();raf=requestAnimationFrame(tick)}}
function resume(){if(!raf&&!state.paused&&state.visible&&!document.hidden){last=performance.now();raf=requestAnimationFrame(tick)}}
function stop(){cancelAnimationFrame(raf);raf=0}
try{
if(new URLSearchParams(location.search).has('fallback'))throw new Error('Requested static preview');
renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,innerWidth<700?1.25:1.5));renderer.outputEncoding=THREE.sRGBEncoding;host.appendChild(renderer.domElement);
scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(35,1,.1,100);camera.position.z=12;
scene.add(new THREE.AmbientLight(0xffffff,.55));const key=new THREE.DirectionalLight(0xffffff,1.8);key.position.set(-4,7,7);scene.add(key);const rim=new THREE.DirectionalLight(0xe04832,.65);rim.position.set(5,-3,3);scene.add(rim);
disc=new THREE.Group();scene.add(disc);
const body=new THREE.Mesh(new THREE.CylinderGeometry(2.8,2.8,.075,160),new THREE.MeshStandardMaterial({color:0x121212,roughness:.26,metalness:.7}));body.rotation.x=Math.PI/2;disc.add(body);
// One radial shader replaces hundreds of individually rendered grooves.
const material=new THREE.ShaderMaterial({side:THREE.DoubleSide,vertexShader:`varying vec2 vUv;varying vec3 vNormal;void main(){vUv=uv;vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,fragmentShader:`precision highp float;varying vec2 vUv;varying vec3 vNormal;void main(){vec2 q=(vUv-.5)*2.;float r=length(q);float a=atan(q.y,q.x);float groove=sin(r*790.)*.5+.5;float band=sin(r*98.)*.5+.5;float sweep=pow(abs(sin(a+.7+vNormal.x*.8)),16.);float sheen=pow(abs(sin(a-1.1)),45.);float ring=step(.32,r)*(.012+groove*.026+band*.008);vec3 col=vec3(.025,.027,.028)+ring;col+=vec3(.30,.30,.285)*sweep*(.38+groove*.22);col+=vec3(.17,.085,.065)*sheen;col*=.8+.2*(1.-r);gl_FragColor=vec4(col,1.);}`});
const face=new THREE.Mesh(new THREE.CircleGeometry(2.8,160),material);face.position.z=.041;disc.add(face);
const edge=new THREE.Mesh(new THREE.TorusGeometry(2.794,.014,6,160),new THREE.MeshStandardMaterial({color:0x888888,roughness:.2,metalness:.9}));edge.position.z=.015;disc.add(edge);
const c=document.createElement('canvas');c.width=c.height=1024;const x=c.getContext('2d');x.fillStyle='#b82e24';x.fillRect(0,0,1024,1024);x.strokeStyle='#641b17';x.lineWidth=2;for(const r of [455,465,477]){x.beginPath();x.arc(512,512,r,0,Math.PI*2);x.stroke()}x.textAlign='center';x.fillStyle='#e8e5dc';x.font='bold 111px Arial';x.fillText('ORÁCULO',512,302);x.font='30px monospace';x.fillText('R E C O R D S',512,354);x.font='22px monospace';x.fillText('PLASTICAL JEWELS',512,737);x.font='17px monospace';x.fillText('FOR DARKWAVE ENTHUSIAST COLLECTORS',512,774);x.textAlign='left';x.fillText('SIDE A',120,520);x.textAlign='right';x.fillText('33 ⅓',904,520);x.beginPath();x.arc(512,512,56,0,Math.PI*2);x.stroke();x.beginPath();x.arc(512,512,18,0,Math.PI*2);x.fillStyle='#171717';x.fill();
const texture=new THREE.CanvasTexture(c);texture.encoding=THREE.sRGBEncoding;const label=new THREE.Mesh(new THREE.CircleGeometry(.96,96),new THREE.MeshBasicMaterial({map:texture}));label.position.z=.048;disc.add(label);disc.rotation.set(.5,-.35,-.18);
function resize(){const r=host.getBoundingClientRect();renderer.setSize(r.width,r.height);camera.aspect=r.width/r.height;camera.position.z=r.width<700?Math.max(15,21*(390/r.width)):12;camera.updateProjectionMatrix();disc.position.x=r.width<700?0:.5;disc.position.y=r.width<700?-.15:-.82;draw()}
state.webgl=true;state.ready=true;resize();
const desktop=()=>innerWidth>=700;
const originalUpdate=update;
update=function(dt){originalUpdate(dt);if(!desktop())disc.position.y=-.15+state.progress*.3};
addEventListener('resize',resize,{passive:true});
hero.addEventListener('pointermove',e=>{if(state.paused)return;const r=hero.getBoundingClientRect();tx=(e.clientX/r.width-.5)*.45;ty=((e.clientY-r.top)/r.height-.5)*.22},{passive:true});
hero.addEventListener('pointerleave',()=>{tx=0;ty=0},{passive:true});
addEventListener('scroll',()=>{state.progress=Math.min(1,Math.max(0,-hero.getBoundingClientRect().top/hero.offsetHeight));},{passive:true});
new IntersectionObserver(([entry])=>{state.visible=entry.isIntersecting;if(state.visible)resume();else stop()},{threshold:0}).observe(hero);
addEventListener('visibilitychange',()=>{if(document.hidden)stop();else resume()});
motion.addEventListener('click',()=>{state.paused=!state.paused;syncButton();if(state.paused)stop();else resume()});
media.addEventListener('change',()=>{state.paused=media.matches;syncButton();if(state.paused)stop();else resume()});
document.getElementById('rotate-left').addEventListener('click',()=>{manual-=.25;update(0);draw()});document.getElementById('rotate-right').addEventListener('click',()=>{manual+=.25;update(0);draw()});
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();stop();state.webgl=false;document.body.classList.add('no-webgl')});renderer.domElement.addEventListener('webglcontextrestored',()=>{state.webgl=true;document.body.classList.remove('no-webgl');draw();resume()});
update(0);draw();resume();
}catch(e){state.error=String(e);document.body.classList.add('no-webgl');state.ready=true;host.setAttribute('aria-label','Static vinyl record illustration');if(!location.search.includes('fallback'))console.warn('Using static record illustration:',e.message)}
})();
