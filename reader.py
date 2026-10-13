"""Interactive browser player with timestamp-driven highlighting and auto-scroll."""
from __future__ import annotations
import base64
import html
import json
import streamlit.components.v1 as components


def show_reader(wav: bytes, words: list[dict], height: int = 400) -> None:
    payload = json.dumps(words).replace("<", "\\u003c")
    data = base64.b64encode(wav).decode("ascii")
    markup = """<!doctype html><html><head><meta charset="utf-8"><style>
    body {font-family:system-ui,sans-serif; color:var(--text-color,#242424); margin:0}
    #reader {height:290px; overflow-y:auto; border:1px solid #9996;
      border-radius:10px; padding:18px; line-height:2.1; font-size:19px}
    .word {border-radius:3px; padding:2px 1px}
    .active {background:#ffdd57; color:#171717; box-shadow:0 0 0 2px #ffdd57}
    audio {width:100%; margin:12px 0} .hint {font-size:12px; opacity:.72}
    </style></head><body>
    <div id="reader" aria-live="off"></div>
    <audio id="audio" controls preload="metadata" src="data:audio/wav;base64,DATA"></audio>
    <div class="hint">Highlighted words are transcribed from the generated audio.
    Speech recognition may omit or misrecognize words. Adjust playback position freely.</div>
    <script>
    const words = WORDS;
    const reader = document.getElementById('reader');
    const audio = document.getElementById('audio');
    words.forEach((item,i) => {
      const span = document.createElement('span');
      span.className='word'; span.textContent=item.text+' ';
      span.id='w'+i;
      reader.appendChild(span);
    });
    let active=-1;
    function update(){
      const t=audio.currentTime;
      let lo=0,hi=words.length-1,found=-1;
      while(lo<=hi){
        const m=(lo+hi)>>1;
        if(words[m].start<=t){found=m;lo=m+1}else{hi=m-1}
      }
      if(found>=0 && t>words[found].end+0.22) found=-1;
      if(found!==active){
        if(active>=0) document.getElementById('w'+active).classList.remove('active');
        active=found;
        if(active>=0){
          const el=document.getElementById('w'+active);
          el.classList.add('active');
          const top=el.offsetTop-reader.offsetTop;
          if(top<reader.scrollTop+55 || top>reader.scrollTop+reader.clientHeight-65)
            reader.scrollTo({top:Math.max(0,top-110),behavior:'smooth'});
        }
      }
      if(!audio.paused) requestAnimationFrame(update);
    }
    audio.addEventListener('play',update);
    audio.addEventListener('seeked',update);
    audio.addEventListener('timeupdate',update);
    </script></body></html>""".replace("WORDS", payload).replace("DATA", data)
    components.html(markup, height=height, scrolling=False)
