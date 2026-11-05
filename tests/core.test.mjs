import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {categories,defaults,readState,stateQuery,filterRows,sortRows,groupCounts,networkData,toCsv,escapeHtml} from '../assets/core.mjs';
const {records,metadata}=JSON.parse(readFileSync(new URL('../data/corpus.json',import.meta.url),'utf8'));
test('totals, honest checking status and duplicate sensitivity',()=>{
 assert.equal(records.length,500);assert.equal(filterRows(records,{...defaults,sensitive:true}).length,500);
 assert.equal(filterRows(records,{...defaults,sensitive:true,unique:true}).length,492);
 assert.equal(filterRows(records,{...defaults,checked:'yes'}).length,0);
 assert.equal(filterRows(records,defaults).length,500-metadata.sensitive_records);
 assert.ok(records.every(r=>r.source.includes('unconfirmed')&&r.human_checked==='no'));
});
test('English, Chinese and compound search',()=>{
 assert.equal(filterRows(records,{...defaults,q:'ATTENTION',sensitive:true}).length,45);
 const chinese=filterRows(records,{...defaults,q:'注意'});
 assert.ok(chinese.length>0&&chinese.every(r=>[r.source_text,r.target_text,r.key_term,r.target_term,r.id].some(v=>v.includes('注意'))));
 assert.equal(filterRows(records,{...defaults,q:'permission',category:'support-verb'}).length,4);
 assert.equal(filterRows(records,{...defaults,q:'nonexistentxyz'}).length,0);
});
test('all category/checking/duplicate/content combinations preserve chart counts',()=>{
 for(const category of ['all',...categories])for(const checked of ['all','yes','no'])for(const unique of [false,true])for(const sensitive of [false,true]){
  const rows=filterRows(records,{...defaults,category,checked,unique,sensitive});
  assert.equal(groupCounts(rows,'category').reduce((n,x)=>n+x[1],0),rows.length);
  assert.equal(groupCounts(rows,'key_term').reduce((n,x)=>n+x[1],0),rows.length);
  const links=networkData(rows,1000,1);assert.equal(links.reduce((n,x)=>n+x.count,0),rows.length);
  for(const l of links)assert.equal(l.count,rows.filter(x=>x.key_term===l.source&&x.target_term===l.target).length);
 }
});
test('network controls restrict display without mutating corpus',()=>{
 const links=networkData(records,3,2);assert.ok(new Set(links.map(l=>l.source)).size<=3);
 assert.ok(links.every(l=>l.count>=2));assert.ok(links.reduce((n,l)=>n+l.count,0)<500);assert.equal(records.length,500);
});
test('URL state round trips and malformed controls are sanitized',()=>{
 const s={...defaults,lang:'zh',q:'注意 & "test"',category:'prepositional',checked:'no',unique:true,sensitive:true,top:16,weight:3,sort:'key_term',dir:'desc',page:3,id:'123'};
 assert.deepEqual(readState(stateQuery(s)),s);
 const bad=readState('?category=unknown&checked=x&top=Infinity&weight=-99&page=NaN&sort=__proto__');
 assert.equal(bad.category,'all');assert.equal(bad.weight,1);assert.equal(bad.top,8);assert.equal(bad.page,1);assert.equal(bad.sort,'id');
});
test('numeric sorting preserves input order',()=>{
 const rows=[{id:'10'},{id:'2'},{id:'1'}];assert.deepEqual(sortRows(rows,defaults).map(x=>x.id),['1','2','10']);assert.deepEqual(rows.map(x=>x.id),['10','2','1']);
});
test('CSV handles Unicode, quoting, multiline text and formula prefixes',()=>{
 const csv=toCsv([{id:'1',source_text:'=HYPERLINK("x")',target_text:'中文\n下一行',key_term:'"quote"'}]);
 assert.ok(csv.startsWith('\uFEFF'));assert.ok(csv.includes('"\'=HYPERLINK(""x"")"'));assert.ok(csv.includes('"中文\n下一行"'));assert.ok(csv.includes('"""quote"""'));assert.equal(toCsv([]).split('\r\n').length,1);
});
test('untrusted text is escaped',()=>{assert.equal(escapeHtml('<img onerror="x">&'),'&lt;img onerror=&quot;x&quot;&gt;&amp;');});
