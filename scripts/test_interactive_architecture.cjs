const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'../publication/redesigned/interactive_architecture.fragment.html'),'utf8');const source=html.match(/<script>([\s\S]*?)<\/script>/)[1];
for(const width of [280,320,560,736]){
 class El{constructor(name){this.name=name;this.attrs={};this.children=[];this.textContent='';}setAttribute(k,v){this.attrs[k]=v;}append(e){this.children.push(e);}replaceChildren(...e){this.children=e;}getBoundingClientRect(){return {width};}addEventListener(k,fn){this[k]=fn;}}
 const mode=new El('select');mode.value='prototype';const select=new El('select'),holder=new El('div'),detail=new El('div');const root={querySelector:s=>({'#routing-mode':mode,'#routing-stage':select,'#routing-diagram':holder,'#routing-detail':detail}[s])};
 const document={getElementById:id=>{assert.equal(id,'routing-feedback-architecture');return root;},createElementNS:(_,name)=>new El(name)};class ResizeObserver{constructor(fn){this.fn=fn;}observe(){this.fn();}}
 vm.runInNewContext(source,{document,ResizeObserver,Math,Number});const descriptions=[];
 for(let i=0;i<6;i++){select.value=String(i);select.change();const svg=holder.children[0];assert.equal(svg.attrs.viewBox.split(' ')[2],String(width));const nodes=svg.children.filter(x=>x.name==='rect');assert.equal(nodes.length,6);assert.equal(nodes.filter(x=>x.attrs.class.includes('active')).length,1);assert.equal(nodes[i].attrs.class,'node active');descriptions.push(detail.textContent);}
 assert.equal(new Set(descriptions).size,6);
}
console.log('PASS: all six component selections at 280, 320, 560 and 736 px; correct active node, viewBox and detail. DOM-level verification only.');
