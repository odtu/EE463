"""Write the report as one self-contained HTML file (works offline)."""

import html
import json
import datetime

from .findings import CATEGORIES, SEVERITY_TEXT

MANUAL_CHECKS = [
    "Print the board 1:1 on paper and put the real parts on it: every footprint must match the part you bought.",
    "Check the pinout of each MOSFET, diode, controller, gate driver and connector against its datasheet.",
    "Ratings: MOSFETs, diodes and capacitors on the input side rated for 48 V plus ringing (60 V or more for switches, 63 V or more for capacitors).",
    "Inductor saturation current above the peak current (output current + half the ripple), with margin; 7.5 A if you go for the overload bonus.",
    "Hot loop: input ceramic capacitor, high-side switch and low-side switch/diode form the smallest possible loop, on one layer, with ground under it.",
    "Gate drive: driver right at the MOSFETs; gate track and its return (source) run side by side; bootstrap capacitor at the driver pins.",
    "Feedback: divider gives 12 V; divider right at the FB pin; feedback track away from the switch node and the inductor.",
    "If you sense current with a shunt: the sense tracks start at the inside edges of the shunt pads (Kelvin connection).",
    "All auxiliary supplies (controller, driver, fan) come from the main input: no second bench supply at the demo.",
    "Thermal: you estimated the losses of each power part and gave it enough copper or a heatsink.",
    "Input and output connectors are labelled with voltage and polarity; consider reverse-polarity protection (bonus).",
    "Open the Gerber and drill files in a Gerber viewer (KiCad GerbView) and look at every layer before you zip them.",
    "The submission contains Gerbers, drill files, schematic, PCB source files and the bill of materials.",
]

_CSS = r"""
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d232b;--mute:#5f6b7a;--line:#e1e5ea;--err:#c62828;--err-bg:#fdecea;
--warn:#a15c00;--warn-bg:#fff4e0;--info:#1f5fa8;--info-bg:#e8f1fb;--ok:#2e7d32;--ok-bg:#e8f5e9;--board:#17201b;--accent:#2b5cab}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--card:#1b1f24;--ink:#e6e9ee;--mute:#9aa5b1;--line:#2c323a;
--err:#ff6b6b;--err-bg:#3a1d1f;--warn:#ffb84d;--warn-bg:#3a2c14;--info:#7fb2ff;--info-bg:#18273d;--ok:#6fcf73;--ok-bg:#1b301d;--accent:#7fa7ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:20px 24px 8px;max-width:1500px;margin:0 auto}h1{margin:0;font-size:24px}h2{font-size:18px;margin:0 0 10px}
.sub{color:var(--mute);font-size:13px}.wrap{max-width:1500px;margin:0 auto;padding:0 24px 40px}
.verdict{margin:14px 0;padding:14px 18px;border-radius:10px;font-weight:600;font-size:16px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.verdict.fail{background:var(--err-bg);color:var(--err)}.verdict.warn{background:var(--warn-bg);color:var(--warn)}.verdict.pass{background:var(--ok-bg);color:var(--ok)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-left:auto}.chip{padding:3px 10px;border-radius:99px;font-size:13px;font-weight:600}
.chip.error{background:var(--err-bg);color:var(--err);border:1px solid var(--err)}.chip.warning{background:var(--warn-bg);color:var(--warn);border:1px solid var(--warn)}
.chip.info{background:var(--info-bg);color:var(--info);border:1px solid var(--info)}.chip.pass{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok)}
.chip.skipped{background:transparent;color:var(--mute);border:1px solid var(--line)}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px;margin-bottom:16px}
.fact{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px}.fact b{display:block;font-size:12px;color:var(--mute);font-weight:500}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px;align-items:start}
@media (max-width:1000px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin-bottom:16px}
.viewer{position:sticky;top:10px}.viewer svg{width:100%;height:min(70vh,640px);background:var(--board);border-radius:8px;touch-action:none;cursor:grab;display:block}
.vbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:8px;font-size:13px}.vbar label{display:flex;gap:4px;align-items:center}
.vbar button,.btn{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:3px 10px;cursor:pointer;font:inherit;font-size:13px}
.coord{color:var(--mute);font-size:12px;margin-left:auto;font-variant-numeric:tabular-nums}
details.check{border-top:1px solid var(--line);padding:8px 0}details.check:first-of-type{border-top:0}
details.check>summary{cursor:pointer;list-style:none;display:flex;gap:10px;align-items:center}
details.check>summary::-webkit-details-marker{display:none}
.dot{width:10px;height:10px;border-radius:50%;flex:none}.dot.error{background:var(--err)}.dot.warning{background:var(--warn)}.dot.info{background:var(--info)}.dot.pass{background:var(--ok)}.dot.skipped{background:var(--line)}
.ctitle{font-weight:600}.cid{color:var(--mute);font-size:12px;margin-left:auto;white-space:nowrap}
.finding{margin:8px 0 8px 20px;padding:10px 12px;border-left:4px solid var(--line);background:var(--bg);border-radius:0 8px 8px 0}
.finding.error{border-color:var(--err)}.finding.warning{border-color:var(--warn)}.finding.info{border-color:var(--info)}.finding.waived{opacity:.55}
.sev{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.03em}.sev.error{color:var(--err)}.sev.warning{color:var(--warn)}.sev.info{color:var(--info)}
.fix{margin-top:4px;font-size:14px}.fix:before{content:"How to fix: ";font-weight:600}
.locs{margin-top:6px;display:flex;flex-wrap:wrap;gap:6px}.loc{font-size:12px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:5px;padding:1px 7px;cursor:pointer;font-family:ui-monospace,Consolas,monospace}
.loc:hover,.loc.on{border-color:var(--accent);color:var(--accent)}
.passed{color:var(--mute);font-size:13px;margin:6px 0 0}.skipnote{color:var(--mute);font-size:13px;margin-left:20px}
ul.found{margin:4px 0 12px;padding-left:20px}ul.found li{margin:2px 0}
ul.manual{list-style:none;padding:0;margin:0}ul.manual li{display:flex;gap:8px;padding:5px 0;border-top:1px solid var(--line)}ul.manual li:first-child{border:0}
code{font-family:ui-monospace,Consolas,monospace;font-size:13px;background:var(--bg);padding:1px 4px;border-radius:4px}
.legend{display:flex;gap:12px;font-size:12px;color:var(--mute);margin-top:6px;flex-wrap:wrap}.legend span{display:flex;gap:4px;align-items:center}
.sw{width:12px;height:12px;border-radius:3px;display:inline-block}
#markers circle.hot{stroke:#fff;fill:rgba(255,255,255,.18)}
"""

_JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const svg = document.getElementById('board');
const NS = 'http://www.w3.org/2000/svg';
let vb = null, base = null;
function el(t, a, p){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);(p||svg).appendChild(e);return e;}
function circ(x,y,r){return `M${x-r} ${y}a${r} ${r} 0 1 0 ${2*r} 0a${r} ${r} 0 1 0 ${-2*r} 0Z`;}
function draw(){
  const g = D.drawing; if(!g){svg.style.display='none';return;}
  const [x0,y0,x1,y1]=g.bbox, m=Math.max(x1-x0,y1-y0)*0.04+1;
  base=[x0-m,y0-m,(x1-x0)+2*m,(y1-y0)+2*m]; vb=base.slice(); setVB();
  const root=el('g',{id:'root'});
  for(const L of g.layers){
    const lg=el('g',{'data-layer':L.id,class:'layer'},root);
    if(L.f.length){let d='';for(const p of L.f){d+='M'+p[0]+' '+p[1];for(let i=2;i<p.length;i+=2)d+='L'+p[i]+' '+p[i+1];d+='Z';}
      el('path',{d,fill:L.color,'fill-opacity':0.35,class:'fill'},lg);}
    const byW={};for(const l of L.l){(byW[l[4]]=byW[l[4]]||[]).push(l);}
    for(const w in byW){let d='';for(const l of byW[w])d+=`M${l[0]} ${l[1]}L${l[2]} ${l[3]}`;
      el('path',{d,stroke:L.color,'stroke-width':Math.max(+w,0.01),'stroke-linecap':'round',fill:'none','stroke-opacity':0.85},lg);}
    let d='';for(const p of L.p){d+='M'+p[0]+' '+p[1];for(let i=2;i<p.length;i+=2)d+='L'+p[i]+' '+p[i+1];d+='Z';}
    for(const c of L.c)d+=circ(c[0],c[1],c[2]);
    if(d)el('path',{d,fill:L.color,'fill-opacity':0.9},lg);
  }
  let dv='';for(const v of g.vias)dv+=circ(v[0],v[1],v[2]);if(dv)el('path',{d:dv,fill:'#c9c9c9'},root);
  let dh='';for(const v of g.vias)dh+=circ(v[0],v[1],v[3]);for(const h of g.holes)dh+=circ(h[0],h[1],h[2]);
  if(dh)el('path',{d:dh,fill:'#0b0f0d'},root);
  let dp='';for(const p of g.parts){const b=p[3];dp+='M'+b[0]+' '+b[1];for(let i=2;i<b.length;i+=2)dp+='L'+b[i]+' '+b[i+1];dp+='Z';}
  if(dp)el('path',{d:dp,fill:'none',stroke:'#e8e8e8','stroke-opacity':0.35,'stroke-width':0.08,class:'parts'},root);
  const lab=el('g',{class:'labels'},root);
  for(const p of g.parts){const t=el('text',{x:p[1],y:p[2],'font-size':0.9,fill:'#f0f0f0','fill-opacity':0.8,'text-anchor':'middle','dominant-baseline':'middle','font-family':'sans-serif'},lab);t.textContent=p[0];}
  let de='';for(const s of g.outline)de+=`M${s[0]} ${s[1]}L${s[2]} ${s[3]}`;
  el('path',{d:de,stroke:'#f2d27a','stroke-width':0.25,fill:'none','stroke-linecap':'round'},root);
  el('g',{id:'markers'},root);
  drawMarkers();
}
function setVB(){svg.setAttribute('viewBox',vb.join(' '));sizeMarkers();}
function sizeMarkers(){const r=vb[2]/70;document.querySelectorAll('#markers circle').forEach(c=>{c.setAttribute('r',c.classList.contains('hot')?r*1.8:r);c.setAttribute('stroke-width',r/3);});}
const SEVC={error:'#ff4d4d',warning:'#ffb020',info:'#5aa7ff'};
function drawMarkers(){
  const mg=document.getElementById('markers'); if(!mg)return; mg.innerHTML='';
  document.querySelectorAll('.loc').forEach(b=>{
    if(b.closest('.waived'))return;
    const x=+b.dataset.x,y=+b.dataset.y; if(isNaN(x))return;
    const c=el('circle',{cx:x,cy:y,r:1,fill:'none',stroke:SEVC[b.dataset.sev]||'#fff'},mg);
    c.dataset.key=b.dataset.key; c.style.cursor='pointer';
    const t=el('title',{},c);t.textContent=b.title;
    c.addEventListener('click',ev=>{ev.stopPropagation();const btn=document.querySelector(`.loc[data-key="${b.dataset.key}"]`);
      if(btn){btn.closest('details').open=true;btn.scrollIntoView({block:'center',behavior:'smooth'});focusLoc(btn,false);}});
  });
  sizeMarkers();
}
function focusLoc(btn,zoom=true){
  document.querySelectorAll('.loc.on').forEach(b=>b.classList.remove('on'));btn.classList.add('on');
  document.querySelectorAll('#markers circle.hot').forEach(c=>c.classList.remove('hot'));
  const c=document.querySelector(`#markers circle[data-key="${btn.dataset.key}"]`);
  if(c){c.classList.add('hot');c.parentNode.appendChild(c);}
  if(zoom&&base){const w=Math.min(base[2],25),h=w*base[3]/base[2];vb=[+btn.dataset.x-w/2,+btn.dataset.y-h/2,w,h];setVB();}
  else sizeMarkers();
}
document.addEventListener('click',e=>{const b=e.target.closest('.loc');if(b){focusLoc(b);if(window.innerWidth<1000)svg.scrollIntoView({behavior:'smooth'});}});
function toPt(ev){const r=svg.getBoundingClientRect();const s=Math.max(vb[2]/r.width,vb[3]/r.height);
  const ox=(r.width*s-vb[2])/2,oy=(r.height*s-vb[3])/2;return [vb[0]-ox+(ev.clientX-r.left)*s, vb[1]-oy+(ev.clientY-r.top)*s, s];}
svg.addEventListener('wheel',ev=>{ev.preventDefault();const [x,y]=toPt(ev);const k=ev.deltaY>0?1.2:1/1.2;
  vb=[x-(x-vb[0])*k,y-(y-vb[1])*k,vb[2]*k,vb[3]*k];setVB();},{passive:false});
let drag=null;
svg.addEventListener('pointerdown',ev=>{drag=[ev.clientX,ev.clientY,vb[0],vb[1],toPt(ev)[2]];svg.setPointerCapture(ev.pointerId);svg.style.cursor='grabbing';});
svg.addEventListener('pointermove',ev=>{const [x,y]=toPt(ev);document.getElementById('coord').textContent=`x ${x.toFixed(2)}  y ${y.toFixed(2)} mm`;
  if(!drag)return;vb[0]=drag[2]-(ev.clientX-drag[0])*drag[4];vb[1]=drag[3]-(ev.clientY-drag[1])*drag[4];setVB();});
svg.addEventListener('pointerup',()=>{drag=null;svg.style.cursor='grab';});
document.getElementById('fit').onclick=()=>{vb=base.slice();setVB();};
document.querySelectorAll('[data-toggle]').forEach(cb=>cb.addEventListener('change',()=>{
  const k=cb.dataset.toggle;
  if(k==='fills')document.querySelectorAll('.fill').forEach(e=>e.style.display=cb.checked?'':'none');
  else if(k==='labels')document.querySelectorAll('.labels').forEach(e=>e.style.display=cb.checked?'':'none');
  else document.querySelectorAll(`.layer[data-layer="${k}"]`).forEach(e=>e.style.display=cb.checked?'':'none');}));
document.querySelectorAll('ul.manual input').forEach((cb,i)=>{const key='pcbcheck-manual-'+D.board+'-'+i;
  try{cb.checked=localStorage.getItem(key)==='1';}catch(e){}
  cb.addEventListener('change',()=>{try{localStorage.setItem(key,cb.checked?'1':'0');}catch(e){}});});
draw();
"""


def _e(s):
    return html.escape(str(s), quote=True)


def render(report, path):
    verdict_cls, verdict_txt = report.verdict()
    counts = report.counts()
    statuses = [report.checks[c].status for c in report.order]
    n_pass = statuses.count("pass")
    parts = []
    w = parts.append
    w("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    w("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    w(f"<title>{_e(report.title)}: {_e(report.board_name)}</title><style>{_CSS}</style></head><body>")
    w("<header>")
    w(f"<h1>{_e(report.title)} &middot; {_e(report.board_name)}</h1>")
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    w(f"<div class='sub'>{_e(report.source)} &middot; checked {when}</div>")
    w(f"<div class='verdict {verdict_cls}'><span>{_e(verdict_txt)}</span><span class='chips'>")
    w(f"<span class='chip error'>{counts['error']} must fix</span><span class='chip warning'>{counts['warning']} should fix</span>"
      f"<span class='chip info'>{counts['info']} to check</span><span class='chip pass'>{n_pass} checks passed</span></span></div>")
    w("</header><div class='wrap'>")
    if report.meta:
        w("<div class='facts'>")
        for k, v in report.meta.items():
            w(f"<div class='fact'><b>{_e(k)}</b>{_e(v)}</div>")
        w("</div>")
    w("<div class='grid'><div>")

    if report.detected:
        w("<div class='card'><h2>What the checker found on your board</h2>")
        w("<p class='sub'>The power checks below rely on this. If something is wrong here, fix the references/net names "
          "or correct it in <code>pcb_checker.json</code> (see the README).</p>")
        for heading, lines in report.detected:
            w(f"<b>{_e(heading)}</b><ul class='found'>")
            for l in lines:
                w(f"<li>{_e(l)}</li>")
            w("</ul>")
        w("</div>")

    key = 0
    for cat, cat_title in CATEGORIES:
        cids = [c for c in report.order if report.checks[c].category == cat]
        if not cids:
            continue
        w(f"<div class='card'><h2>{_e(cat_title)}</h2>")
        passed = []
        for cid in cids:
            ch = report.checks[cid]
            st = ch.status
            if st == "pass":
                passed.append(ch.title)
                continue
            is_open = " open" if st in ("error", "warning") else ""
            w(f"<details class='check'{is_open}><summary><span class='dot {st}'></span><span class='ctitle'>{_e(ch.title)}</span>"
              f"<span class='cid'>{_e(cid)}{(' · ' + _e(ch.rule)) if ch.rule else ''}</span></summary>")
            if ch.skipped:
                w(f"<div class='skipnote'>Not checked: {_e(ch.skipped)}</div>")
            for f in ch.findings:
                wv = " waived" if f.waived else ""
                w(f"<div class='finding {f.severity}{wv}'><span class='sev {f.severity}'>{_e(SEVERITY_TEXT[f.severity])}</span>"
                  + (f" <span class='sub'>(waived: {_e(f.waived)})</span>" if f.waived else "")
                  + f"<div>{_e(f.message)}</div>")
                if f.fix:
                    w(f"<div class='fix'>{_e(f.fix)}</div>")
                if f.locations:
                    w("<div class='locs'>")
                    for (x, y, layer, label) in f.locations:
                        key += 1
                        tip = f"{label} @ ({x:.2f}, {y:.2f}) {layer}".strip()
                        w(f"<button class='loc' data-key='k{key}' data-sev='{f.severity}' data-x='{x:.3f}' data-y='{y:.3f}' "
                          f"title='{_e(tip)}'>{_e(label or f'{x:.1f}, {y:.1f}')}</button>")
                    w("</div>")
                w("</div>")
            w("</details>")
        if passed:
            w(f"<p class='passed'><span class='chip pass'>passed</span> {_e(' · '.join(passed))}</p>")
        w("</div>")

    w("<div class='card'><h2>Check these yourself</h2><p class='sub'>A program cannot see these. Tick them off as you go "
      "(the ticks are saved in this browser only).</p><ul class='manual'>")
    for m in report.manual or MANUAL_CHECKS:
        w(f"<li><input type='checkbox'><span>{_e(m)}</span></li>")
    w("</ul></div>")

    if report.notes or report.settings:
        w("<div class='card'><h2>Settings and notes</h2><ul class='found'>")
        for k, v in report.settings.items():
            w(f"<li><b>{_e(k)}:</b> {_e(v)}</li>")
        for n in report.notes:
            w(f"<li>{_e(n)}</li>")
        w("</ul></div>")
    w("</div>")

    w("<div><div class='card viewer'><div class='vbar'><b>Board</b>")
    if report.drawing:
        for L in report.drawing["layers"]:
            w(f"<label><input type='checkbox' checked data-toggle='{_e(L['id'])}'><span class='sw' style='background:{L['color']}'></span>{_e(L['label'])}</label>")
        w("<label><input type='checkbox' checked data-toggle='fills'>Pours</label>")
        if report.drawing.get("parts"):
            w("<label><input type='checkbox' checked data-toggle='labels'>Names</label>")
    w("<button id='fit'>Fit</button><span class='coord' id='coord'></span></div>")
    w("<svg id='board' xmlns='http://www.w3.org/2000/svg' preserveAspectRatio='xMidYMid meet'></svg>")
    w("<div class='legend'><span><span class='sw' style='border:2px solid #ff4d4d'></span>must fix</span>"
      "<span><span class='sw' style='border:2px solid #ffb020'></span>should fix</span>"
      "<span><span class='sw' style='border:2px solid #5aa7ff'></span>check</span>"
      "<span>Scroll to zoom, drag to move, click a marker or a location button to jump.</span></div></div></div></div>")
    data = {"board": report.board_name, "drawing": report.drawing}
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    w(f"<script id='data' type='application/json'>{blob}</script><script>{_JS}</script>")
    w("</div></body></html>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))
    return path
