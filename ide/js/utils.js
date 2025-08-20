(function(){
  function debounce(fn, delay){
    let t; return function(){ const ctx=this, args=arguments; clearTimeout(t); t=setTimeout(function(){ fn.apply(ctx,args); }, delay); };
  }

  function xmlTextToDom(text){
    try {
      if (window.Blockly && Blockly.utils && Blockly.utils.xml && Blockly.utils.xml.textToDom) return Blockly.utils.xml.textToDom(text);
      if (window.Blockly && Blockly.Xml && Blockly.Xml.textToDom) return Blockly.Xml.textToDom(text);
    } catch(e) { console.warn('xmlTextToDom fallback', e); }
    try { const doc = new DOMParser().parseFromString(text, 'text/xml'); return doc && (doc.documentElement || doc); } catch(e){ return null; }
  }
  function xmlDomToText(dom){
    try {
      if (window.Blockly && Blockly.utils && Blockly.utils.xml && Blockly.utils.xml.domToText) return Blockly.utils.xml.domToText(dom);
      if (window.Blockly && Blockly.Xml && Blockly.Xml.domToText) return Blockly.Xml.domToText(dom);
    } catch(e) { console.warn('xmlDomToText fallback', e); }
    try { return new XMLSerializer().serializeToString(dom); } catch(e){ return ''; }
  }
  // Shim missing Blockly.Xml methods to utils.xml where needed
  try {
    if (window.Blockly) {
      window.Blockly.Xml = window.Blockly.Xml || {};
      if (!window.Blockly.Xml.textToDom && window.Blockly.utils?.xml?.textToDom) {
        window.Blockly.Xml.textToDom = function(t){ return window.Blockly.utils.xml.textToDom(t); };
      }
      if (!window.Blockly.Xml.domToText && window.Blockly.utils?.xml?.domToText) {
        window.Blockly.Xml.domToText = function(d){ return window.Blockly.utils.xml.domToText(d); };
      }
    }
  } catch(e){ console.warn('Blockly XML shim failed', e); }

  function timestampString(){ const d=new Date(); const pad=n=>String(n).padStart(2,'0'); return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`; }

  window.Utils = { debounce, xmlTextToDom, xmlDomToText, timestampString };
})();
