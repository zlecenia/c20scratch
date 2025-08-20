// Preview module: encapsulates preview rendering and code execution
(function(){
  'use strict';

  // Write HTML into the preview iframe via Blob URL to avoid srcdoc escaping and keep sandbox strict
  function writeIframeHTML(html){
    try {
      const iframe = document.getElementById('preview');
      if (!iframe) return;
      // Revoke previous blob URL if any
      if (window.__previewBlobURL) {
        try { URL.revokeObjectURL(window.__previewBlobURL); } catch(_){ }
        window.__previewBlobURL = null;
      }
      const blob = new Blob([html], {type: 'text/html;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      window.__previewBlobURL = url;
      iframe.src = url;
    } catch(e){ console.error('Preview render failed', e); }
  }

  // Build a full HTML document string used for the sandboxed iframe
  function buildIframeHTML(code){
    // Encode generated code to Base64 to avoid unescaped line breaks in string literals
    let __b64;
    try {
      __b64 = btoa(unescape(encodeURIComponent(code)));
    } catch(_) {
      // Fallback without unicode handling
      __b64 = btoa(code);
    }
    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <style>
      body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;padding:12px;}
      .c20-b{position:relative;}
      .c20-highlight{outline:2px solid #1976d2; background:rgba(25,118,210,0.08); outline-offset:2px;}
    </style>
</head>
<body>
    <div id="app"></div>
    <script>
        let views = [];
        let htmlOutput = "";
        // Base URL of the parent app (used for API calls from sandboxed iframe)
        const API_BASE = ${JSON.stringify(window.location.origin)};
        // Helper to wrap HTML with block id for preview highlighting
        function appendHtmlWithBid(bid, html){
          const id = bid || '';
          htmlOutput += '<span class="c20-b" data-bid="'+id+'">'+html+'</span>';
        }
        // Highlighting support inside iframe
        let __hl = [];
        function __clearHighlight(){ __hl.forEach(el=>el.classList.remove('c20-highlight')); __hl = []; }
        function highlightByBlockId(bid){
          __clearHighlight();
          if (!bid) return;
          const nodes = document.querySelectorAll('[data-bid="'+bid+'"]');
          nodes.forEach(el=>{
            el.classList.add('c20-highlight');
            try { el.scrollIntoView({block:'nearest', inline:'nearest', behavior:'smooth'}); } catch(_){ }
          });
          __hl = Array.from(nodes);
        }
        window.addEventListener('message', (ev)=>{
          const d = ev && ev.data || {};
          if (d && d.type === 'highlight') highlightByBlockId(d.blockId);
        });
        // Execute generated code safely; surface syntax/runtime errors
        try {
          const __b64Str = "${__b64}";
          // Decode Base64 with unicode support
          const __userCode = decodeURIComponent(escape(atob(__b64Str)));
          const __wrapped = "(function(){\n" + __userCode + "\n})();";
          eval(__wrapped);
        } catch(e) {
          console.error('Generated code error:', e);
          try {
            const pre = document.createElement('pre');
            pre.textContent = 'Error: ' + (e && e.message ? e.message : String(e));
            document.body.insertBefore(pre, document.body.firstChild);
          } catch(_){ }
        }
        let finalHTML = "";
        views.forEach(v=>{
          const bid = v && v.bid ? ' data-bid="'+v.bid+'"' : '';
          finalHTML += '<section'+bid+' id="'+v.name+'">'+v.html+'</section>';
        });
        finalHTML += htmlOutput;
        document.getElementById('app').innerHTML = finalHTML;
    <\/script>
</body>
</html>`;
  }

  // Generate code from Blockly and render preview
  function runCode(){
    try {
      let code = "";
      try {
        const ws = window.workspace; // exposed from index.html
        code = (window.Blockly && window.Blockly.JavaScript && ws)
          ? window.Blockly.JavaScript.workspaceToCode(ws)
          : "";
      } catch (e) {
        console.error("Error generating code from workspace:", e);
        // Show error in preview
        const errHTML = `<!DOCTYPE html><html><body>
                <h3>Error generating code:</h3>
                <pre>${(e && e.message) ? e.message.replace(/[<>&]/g, s=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[s])) : 'Unknown error'}</pre>
                <p>Please check that all blocks have proper generators defined.</p>
            </body></html>`;
        window.lastIframeHTML = errHTML;
        if (typeof window.setEditorValue === 'function') window.setEditorValue(errHTML);
        writeIframeHTML(errHTML);
        return;
      }

      // Create a complete HTML document structure for the iframe
      const iframeContent = buildIframeHTML(code);
      window.lastIframeHTML = iframeContent;
      if (typeof window.setEditorValue === 'function') window.setEditorValue(iframeContent);
      writeIframeHTML(iframeContent);
    } catch (e) {
      console.error("Error in runCode:", e);
    }
  }

  // Expose API
  window.Preview = {
    writeIframeHTML,
    buildIframeHTML,
    runCode,
  };
})();
