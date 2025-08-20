(function(){
  // Module Management State
  const activeModules = new Set(['ui', 'values']); // Core modules always active
  let availableModules = [];

  async function openModuleManager() {
    const el = document.getElementById('moduleModal');
    if (el) el.style.display = 'block';
    await loadAvailableModules();
    updateActiveModulesList();
  }

  function closeModuleManager() {
    const el = document.getElementById('moduleModal');
    if (el) el.style.display = 'none';
  }

  async function loadAvailableModules() {
    try {
      const response = await fetch('/modules/list');
      const data = await response.json();
      availableModules = data.modules || [];
      renderModulesList();
    } catch (e) {
      console.error('Failed to load modules:', e);
    }
  }

  function renderModulesList() {
    const container = document.getElementById('modulesList');
    if (!container) return;
    container.innerHTML = '';

    availableModules.forEach(module => {
      const moduleDiv = document.createElement('div');
      moduleDiv.style.cssText = 'border:1px solid #ddd; margin:5px 0; padding:10px; border-radius:4px;';

      const isActive = activeModules.has(module.id);
      const isCoreModule = module.type === 'core';

      moduleDiv.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${module.name}</strong> <span style="color:#666;">(${module.type})</span>
            <br><small>${module.description}</small>
          </div>
          <div>
            ${isActive ? 
              `<button onclick="deactivateModule('${module.id}')" ${isCoreModule ? 'disabled' : ''}>
                 ${isCoreModule ? '🔒 Core' : '✅ Active'}
               </button>` :
              `<button onclick="activateModule('${module.id}')">➕ Activate</button>`
            }
          </div>
        </div>
      `;
      container.appendChild(moduleDiv);
    });
  }

  async function activateModule(moduleId) {
    try {
      activeModules.add(moduleId);
      await loadModuleBlocks(moduleId);
      renderModulesList();
      updateActiveModulesList();
      console.log(`Module ${moduleId} activated`);
    } catch (e) {
      console.error(`Failed to activate module ${moduleId}:`, e);
      activeModules.delete(moduleId);
    }
  }

  function deactivateModule(moduleId) {
    const module = availableModules.find(m => m.id === moduleId);
    if (module && module.type !== 'core') {
      activeModules.delete(moduleId);
      // Note: Removing blocks from the toolbox would need a more complex implementation
      renderModulesList();
      updateActiveModulesList();
      console.log(`Module ${moduleId} deactivated`);
    }
  }

  function updateActiveModulesList() {
    const container = document.getElementById('activeModulesList');
    if (!container) return;
    container.innerHTML = '';

    const activeList = Array.from(activeModules).map(id => {
      const module = availableModules.find(m => m.id === id);
      return module ? module.name : id;
    }).join(', ');

    container.innerHTML = `<p>Active: ${activeList}</p>`;
  }

  async function loadModuleBlocks(moduleId) {
    try {
      const response = await fetch(`/modules/${moduleId}/spec`);
      const spec = await response.json();

      // Prefer modular generators if available, fallback to inline
      const gens = (window && window.ModuleGenerators) || {};
      if (moduleId === 'linkedin') {
        const fn = gens.generateLinkedInBlocks || window.generateLinkedInBlocks;
        if (typeof fn === 'function') fn(spec); else console.warn('LinkedIn generator not available');
      } else if (moduleId === 'openai') {
        const fn = gens.generateOpenAIBlocks || window.generateOpenAIBlocks;
        if (typeof fn === 'function') fn(spec); else console.warn('OpenAI generator not available');
      } else if (moduleId === 'mcp') {
        const fn = gens.generateMCPBlocks || window.generateMCPBlocks;
        if (typeof fn === 'function') fn(spec); else console.warn('MCP generator not available');
      }

      // Refresh toolbox with proper error handling
      try {
        const toolboxElement = document.getElementById('toolbox');
        const workspace = window.workspace; // workspace is created in index.html
        if (toolboxElement && workspace && workspace.updateToolbox) {
          workspace.updateToolbox(toolboxElement);
        }
      } catch(e) {
        console.warn('Module toolbox update failed:', e);
      }
    } catch (e) {
      console.error(`Failed to load blocks for module ${moduleId}:`, e);
    }
  }

  async function uploadModuleFile(event) {
    const file = event?.target?.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/modules/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (response.ok) {
        alert('Module uploaded successfully!');
        await loadAvailableModules();
      } else {
        alert('Upload failed: ' + result.error);
      }
    } catch (e) {
      alert('Upload error: ' + e.message);
    }

    // Reset file input
    try { if (event && event.target) event.target.value = ''; } catch(_){ }
  }

  // Expose to global for index.html event handlers
  window.openModuleManager = openModuleManager;
  window.closeModuleManager = closeModuleManager;
  window.activateModule = activateModule;
  window.deactivateModule = deactivateModule;
  window.loadAvailableModules = loadAvailableModules;
  window.renderModulesList = renderModulesList;
  window.updateActiveModulesList = updateActiveModulesList;
  window.loadModuleBlocks = loadModuleBlocks;
  window.uploadModuleFile = uploadModuleFile;

  // Helpful access to state (read-only usage recommended)
  window.ModuleManagerState = {
    get activeModules(){ return activeModules; },
    get availableModules(){ return availableModules; }
  };
})();
