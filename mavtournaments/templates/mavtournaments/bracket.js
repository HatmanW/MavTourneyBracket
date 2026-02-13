(function(){
  console.log("SUCCESS");
  const svg = document.getElementById('svg');
  if(!svg) return;
  let scale = 1, tx = 0, ty = 0, panning=false, lx=0, ly=0;

  function apply(){ svg.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`; svg.style.transformOrigin='0 0'; }
  function fit(){ scale = Math.min(window.innerWidth / svg.viewBox.baseVal.width, (window.innerHeight-160) / svg.viewBox.baseVal.height); tx = 0; ty = 0; apply(); }
  window.zoomIn = ()=>{ scale *= 1.2; apply(); }
  window.zoomOut = ()=>{ scale /= 1.2; apply(); }
  window.resetView = fit;

  const stage = document.getElementById('stage');
  stage.addEventListener('pointerdown', e=>{ panning=true; lx=e.clientX; ly=e.clientY; stage.setPointerCapture(e.pointerId); });
  stage.addEventListener('pointermove', e=>{ if(!panning) return; tx += (e.clientX - lx); ty += (e.clientY - ly); lx=e.clientX; ly=e.clientY; apply(); });
  stage.addEventListener('pointerup', ()=> panning=false);
  window.addEventListener('resize', fit);
  fit();
})();
