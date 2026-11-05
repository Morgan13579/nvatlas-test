export const categories = ['support-verb', 'prepositional', 'standalone', 'other-frame', 'review'];
export const colors = { 'support-verb':'#a55139', prepositional:'#486f7c', standalone:'#987940', 'other-frame':'#6c7e68', review:'#9a6a89' };
export const defaults = {lang:'en',q:'',category:'all',checked:'all',unique:false,sensitive:false,top:8,weight:1,sort:'id',dir:'asc',page:1,id:''};
export function readState(search) {
  const p=new URLSearchParams(search), s={...defaults};
  s.lang=p.get('lang')==='zh'?'zh':'en';
  s.q=(p.get('q')||'').slice(0,300); s.id=p.get('id')||'';
  s.category=categories.includes(p.get('category'))?p.get('category'):'all';
  s.checked=['yes','no'].includes(p.get('checked'))?p.get('checked'):'all';
  s.unique=p.get('unique')==='1'; s.sensitive=p.get('sensitive')==='1';
  for(const [key,min,max] of [['top',3,20],['weight',1,50],['page',1,100000]]) {
    const v=Number(p.get(key)); s[key]=p.has(key)&&Number.isFinite(v)?Math.min(max,Math.max(min,Math.floor(v))):defaults[key];
  }
  s.sort=['id','source_text','target_text','key_term','category','human_checked'].includes(p.get('sort'))?p.get('sort'):'id';
  s.dir=p.get('dir')==='desc'?'desc':'asc'; return s;
}
export function stateQuery(s) {
  const p=new URLSearchParams();
  for(const [key,value] of Object.entries(s)) if(value!==defaults[key]) p.set(key,typeof value==='boolean'?(value?'1':'0'):String(value));
  return p.toString();
}
export function filterRows(rows,s) {
  const q=s.q.trim().toLocaleLowerCase();
  return rows.filter(r=>(!q||[r.source_text,r.target_text,r.key_term,r.target_term,r.id].some(x=>x.toLocaleLowerCase().includes(q))) &&
    (s.category==='all'||r.category===s.category) && (s.checked==='all'||r.human_checked===s.checked) &&
    (!s.unique||!r.duplicate_of) && (s.sensitive||!r.sensitive) && (!s.id||r.id===s.id));
}
export function sortRows(rows,s) {
  return [...rows].sort((a,b)=>String(a[s.sort]).localeCompare(String(b[s.sort]),s.lang==='zh'?'zh-Hant':'en',{numeric:true})*(s.dir==='asc'?1:-1));
}
export function groupCounts(rows,key) {
  const counts=new Map(); rows.forEach(r=>counts.set(r[key],(counts.get(r[key])||0)+1));
  return [...counts].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])));
}
export function networkData(rows,top,weight) {
  const terms=new Set(groupCounts(rows,'key_term').slice(0,top).map(x=>x[0]));
  const links=new Map();
  for(const r of rows) if(terms.has(r.key_term)) {
    const key=JSON.stringify([r.key_term,r.target_term]);
    if(!links.has(key)) links.set(key,{source:r.key_term,target:r.target_term,count:0});
    links.get(key).count++;
  }
  return [...links.values()].filter(x=>x.count>=weight).sort((a,b)=>b.count-a.count||a.source.localeCompare(b.source));
}
export const exportFields=['id','source_text','target_text','source','source_url','category','human_checked','unit','key_term','target_term','annotation_status','duplicate_of','sensitive'];
export function toCsv(rows) {
  const cell=v=>{let s=String(v??''); if(/^[\s]*[=+@-]/.test(s)) s="'"+s; return '"'+s.replaceAll('"','""')+'"';};
  return '\uFEFF'+[exportFields.join(','),...rows.map(r=>exportFields.map(k=>cell(r[k])).join(','))].join('\r\n');
}
export function escapeHtml(value) {return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
