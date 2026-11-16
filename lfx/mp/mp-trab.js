/* S384 (16/11/2026) — MODO DE TESTE (?camt=1): a leitura do rosto da Mochi roda aqui, num trabalhador ao lado, para não segurar o fio que desenha a tela.
   Recebe um recorte da imagem da câmera, devolve só os pontos do rosto (nada é guardado nem enviado). Se algo falhar, a página volta sozinha ao jeito normal. */
var lm=null,del='';
self.onmessage=function(e){var d=e.data;
  if(d.t==='ini'){
    import(d.base+'vision_bundle.mjs').then(function(V){return V.FilesetResolver.forVisionTasks(d.base.replace(/\/$/,'')).then(function(fs){
      var op=function(x){return {baseOptions:{modelAssetPath:d.base+'face_landmarker.task',delegate:x},runningMode:'IMAGE',numFaces:1}};
      return V.FaceLandmarker.createFromOptions(fs,op('GPU')).then(function(m){del='GPU';return m},function(){del='CPU';return V.FaceLandmarker.createFromOptions(fs,op('CPU'))})})})
    .then(function(m){lm=m;self.postMessage({t:'ok',del:del})},function(er){self.postMessage({t:'erro',m:String(er&&er.message||er)})});
    return}
  if(d.t==='img'){var out=null,ms=0;
    try{var t0=performance.now(),r=lm.detect(d.bm),f=r&&r.faceLandmarks&&r.faceLandmarks[0];ms=performance.now()-t0;
      if(f&&f.length>=478){out=new Float32Array(956);for(var i=0;i<478;i++){out[2*i]=f[i].x;out[2*i+1]=f[i].y}}}
    catch(er){try{d.bm.close()}catch(_){}self.postMessage({t:'r',id:d.id,erro:String(er&&er.message||er)});return}
    try{d.bm.close()}catch(_){}
    self.postMessage({t:'r',id:d.id,P:out,ms:ms},out?[out.buffer]:[])}};
