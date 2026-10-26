export default function({data,parentElement,setTriggerValue}) {
 const root=parentElement.querySelector('.money-grid');
 const previous=new Map([...root.children].map(el=>[el.dataset.tone,Number(el.dataset.cents)]));
 root.classList.toggle('light',data.light);
 root.replaceChildren();
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const frames=[];
 const disposers=[];
 data.items.forEach((item,index)=>{
  const card=document.createElement('article');card.className='money-card '+item.tone;card.dataset.tone=item.tone;card.dataset.cents=item.cents;card.style.setProperty('--delay',`${index*55}ms`);
  const label=document.createElement('div');label.className='money-label';
  const icon=document.createElement('span');icon.className='money-icon';const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('fill','none');svg.setAttribute('stroke','currentColor');svg.setAttribute('stroke-width','1.8');svg.setAttribute('stroke-linecap','round');svg.setAttribute('stroke-linejoin','round');
  const paths={income:['M12 20V4','m5 11 7-7 7 7'],expense:['M12 4v16','m5 13 7 7 7-7','M18 4v5h5'],balance:['M20 8V5H4v15h16V8H4','M16 11h6v5h-6z'],savings:['M19 5a9 9 0 1 0 2 8','M16 8a5 5 0 1 0 1 5','m12 12 9-9','M16 3h5v5']};
  for(const d of paths[item.tone]){const path=document.createElementNS(ns,'path');path.setAttribute('d',d);svg.append(path);}icon.append(svg);icon.setAttribute('aria-hidden','true');
  const title=document.createElement('span');title.textContent=item.label;label.append(icon,title);
  const value=document.createElement('div');value.className='money-value';value.setAttribute('aria-label',item.formatted);
  const visible=document.createElement('span');visible.setAttribute('aria-hidden','true');visible.textContent=item.formatted;value.append(visible);
  const note=document.createElement('div');note.className='money-note';note.textContent=item.note;
  const rail=document.createElement('div');rail.className='status-rail';rail.setAttribute('aria-hidden','true');
  card.append(label,value,note);
  if(['income','expense','savings'].includes(item.tone)){
   card.classList.add('record-card');
   card.setAttribute('role','button');card.tabIndex=0;
   const actionLabel=item.tone==='savings'?'Add savings record':`Add ${item.tone} record`;
   card.setAttribute('aria-label',`${item.label}: ${item.formatted}. ${actionLabel}`);
   const hint=document.createElement('div');hint.className='card-add-hint';hint.textContent='+ '+actionLabel;card.append(hint);
   const activate=()=>setTriggerValue('add_record',item.tone);
   const key=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}};
   card.addEventListener('click',activate);card.addEventListener('keydown',key);
   disposers.push(()=>{card.removeEventListener('click',activate);card.removeEventListener('keydown',key);});
  }
  if(data.history[item.tone]){
   const bars=document.createElement('div');bars.className='mini-bars';bars.setAttribute('aria-label','Monthly '+item.label.toLowerCase()+' over the last twelve months');
   const values=data.history[item.tone];const max=Math.max(...values,1);
   values.forEach(v=>{const bar=document.createElement('i');bar.style.height=(v/max*30+2)+'px';bar.title='J$'+(v/100).toFixed(2);bars.append(bar);});card.append(bars);
  }else if(item.tone==='savings'){
   const track=document.createElement('div');track.className='goal-track';const fill=document.createElement('div');fill.style.width=(data.progress*100)+'%';track.append(fill);track.setAttribute('aria-label',Math.round(data.progress*100)+'% of savings targets');card.append(track);
  }else{card.append(rail);}
  const frame=document.createElement('div');frame.className='instrument-frame';frame.setAttribute('aria-hidden','true');
  const outline=document.createElementNS(ns,'svg');outline.setAttribute('viewBox','0 0 300 180');outline.setAttribute('preserveAspectRatio','none');
  for(const [d,cls] of [['M20 2H280L298 20V160L280 178H20L2 160V20Z','frame-outer'],['M22 8H278L292 23V157L278 172H22L8 157V23Z','frame-inner'],['M3 35V20L20 3H75 M225 177H280L297 160V137','frame-light']]){const line=document.createElementNS(ns,'path');line.setAttribute('d',d);line.setAttribute('class',cls);outline.append(line);}frame.append(outline);card.append(frame);root.append(card);
  const start=previous.get(item.tone);
  // Pointer events cover mice, pens and phone touches without blocking scrolling.
  let tiltFrame=0;
  const reset=()=>{
   cancelAnimationFrame(tiltFrame);
   card.classList.remove('glass-active');
   card.style.setProperty('--tilt-x','0deg');
   card.style.setProperty('--tilt-y','0deg');
  };
  const move=e=>{
   if(reduced.matches || !e.isPrimary)return;
   const rect=card.getBoundingClientRect();
   const x=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
   const y=Math.max(0,Math.min(1,(e.clientY-rect.top)/rect.height));
   cancelAnimationFrame(tiltFrame);
   tiltFrame=requestAnimationFrame(()=>{
    card.classList.add('glass-active');
    const strength=e.pointerType==='touch'?4:7;
    card.style.setProperty('--tilt-x',`${(0.5-y)*strength*2}deg`);
    card.style.setProperty('--tilt-y',`${(x-0.5)*strength*2}deg`);
    card.style.setProperty('--spot-x',`${x*100}%`);
    card.style.setProperty('--spot-y',`${y*100}%`);
   });
  };
  const release=e=>{if(e.pointerType!=='mouse')reset();};
  for(const [event,handler] of [['pointerdown',move],['pointermove',move],['pointerleave',reset],['pointercancel',reset],['pointerup',release]]){
   card.addEventListener(event,handler,{passive:true});
   disposers.push(()=>card.removeEventListener(event,handler));
  }
  reduced.addEventListener('change',reset);
  disposers.push(()=>{reset();reduced.removeEventListener('change',reset);});
  if(start!==undefined && start!==item.cents){
   card.classList.add('updated');const begun=performance.now();
   const step=now=>{const t=Math.min(1,(now-begun)/380);visible.textContent=(t===1||reduced.matches)?item.formatted:'J$'+((start+(item.cents-start)*(1-Math.pow(1-t,3)))/100).toLocaleString('en-JM',{minimumFractionDigits:2,maximumFractionDigits:2});if(t<1&&!reduced.matches)frames.push(requestAnimationFrame(step));};
   if(!reduced.matches)frames.push(requestAnimationFrame(step));
  }
 });
 return ()=>{frames.forEach(cancelAnimationFrame);disposers.forEach(dispose=>dispose());};
}
