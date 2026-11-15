const assert=require('assert');
function detect(r,s){const p=new Map(r.map(x=>[+x.vmid,x]));const id=x=>{const m=[x.name,x.description,x.info?.connect_as].filter(Boolean).join(' ').match(/(?:ct|vm)[-_ ]?(\d{2,6})/i);return m?+m[1]:null};const d=s.map(x=>({id:x.id,status:x.status??'unknown',stacks:Number(x.stack_count??(x.stacks?.length||0)),vmid:id(x)})).filter(x=>x.vmid!==null&&p.has(x.vmid));const g={};for(const x of d)(g[x.vmid]??=[]).push(x);return Object.entries(g).filter(([,v])=>v.length>=2)}
const r=[{vmid:145,node:'pc1'},{vmid:146,node:'pc1'}];
assert.equal(detect(r,[{id:'a',name:'pc1-ct145-tom'}]).length,0);
assert.equal(detect(r,[{id:'a',name:'pc1-ct145-tom'},{id:'b',name:'pc1-ct145-darkbeast'}]).length,1);
assert.equal(detect(r,[{id:'a',name:'pc1-ct145-tom'},{id:'b',name:'pc1-ct145-darkbeast'},{id:'c',name:'pc1-ct145-other'}])[0][1].length,3);
assert.equal(detect(r,[{id:'a',name:'pc1-ct145-tom',status:'NotOk'},{id:'b',name:'pc1-ct145-darkbeast',stacks:[{}]}])[0][1][0].status,'NotOk');
assert.equal(detect(r,[{id:'a',name:'pc1-ct145-tom',stacks:[{}]},{id:'b',name:'pc1-ct145-darkbeast'}])[0][1][0].stacks,1);
console.log('komodo duplicate synthetic tests: ok');
