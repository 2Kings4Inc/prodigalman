(function(){
  var t=document.querySelector('.nav-toggle'),n=document.getElementById('nav');
  if(t&&n){t.addEventListener('click',function(){var o=n.classList.toggle('is-open');t.setAttribute('aria-expanded',o?'true':'false');});}
  // Contact form: send in the background and go to the thanks page at once
  // (FormSubmit's own redirect can take 5-10 seconds). Falls back to a normal
  // post if fetch is missing or FormSubmit rejects the message.
  var form=document.querySelector('form.form');
  if(form&&window.fetch&&window.FormData&&/formsubmit\.co\//.test(form.action)){
    form.addEventListener('submit',function(e){
      e.preventDefault();
      var btn=form.querySelector('button[type=submit]');
      if(btn){btn.disabled=true;btn.textContent='Sending...';}
      var nextEl=form.querySelector('[name=_next]');
      var next=nextEl?nextEl.value:'/thanks/';
      var ajax=form.action.replace('formsubmit.co/','formsubmit.co/ajax/');
      var done=false;
      function go(){if(done)return;done=true;window.location.href=next;}
      function fallback(){if(done)return;done=true;form.submit();}
      var timer=setTimeout(go,1500);
      fetch(ajax,{method:'POST',body:new FormData(form),headers:{'Accept':'application/json'},keepalive:true})
        .then(function(r){return r.json().catch(function(){return {success:r.ok};});})
        .then(function(j){clearTimeout(timer);if(j&&(j.success===true||j.success==='true'))go();else fallback();})
        .catch(function(){clearTimeout(timer);fallback();});
    });
  }
  document.querySelectorAll('.video[data-yt]').forEach(function(v){
    v.addEventListener('click',function(e){
      e.preventDefault();
      var id=v.getAttribute('data-yt');
      var f=document.createElement('iframe');
      f.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&rel=0';
      f.title=v.getAttribute('aria-label')||'YouTube video';
      f.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      f.allowFullscreen=true;
      v.innerHTML='';v.appendChild(f);
    });
  });
})();
