// MCP module block generator
// Exports: generateMCPBlocks(spec)

export function generateMCPBlocks(spec) {
  // Add MCP category with safety checks
  let mcpCategory = document.getElementById('mcpCategory');
  if (!mcpCategory) {
    mcpCategory = document.createElement('category');
    mcpCategory.id = 'mcpCategory';
    mcpCategory.setAttribute('name', 'MCP');
    mcpCategory.setAttribute('colour', '45');

    const toolbox = document.getElementById('toolbox');
    if (toolbox) {
      toolbox.appendChild(mcpCategory);
    } else {
      console.warn('Toolbox element not found for MCP category');
      return;
    }
  }

  // Clear existing blocks to prevent conflicts
  try {
    mcpCategory.innerHTML = '';
  } catch (e) {
    console.warn('Could not clear MCP category:', e);
  }

  Object.entries(spec.blocks || {}).forEach(([blockId, blockSpec]) => {
    const blockName = `mcp_${blockId}`;

    const blockEl = document.createElement('block');
    blockEl.setAttribute('type', blockName);
    mcpCategory.appendChild(blockEl);

    Blockly.Blocks[blockName] = {
      init: function () {
        this.appendDummyInput().appendField(`🔧 ${blockSpec.summary}`);

        if (blockSpec.params) {
          blockSpec.params.forEach((param) => {
            this.appendValueInput(param.name.toUpperCase())
              .appendField(`${param.name}:`)
              .setCheck(['String', 'Number']);
          });
        }

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(45);
      },
    };

    const generateCode = function () {
      return `
        htmlOutput += '<div id="${blockName}">Calling MCP tool...</div>';
        fetch("${spec.base_url}${blockSpec.path}", {
          method: "${blockSpec.method}",
          headers: {'Content-Type': 'application/json'}
        })
        .then(r => r.json())
        .then(data => {
          document.getElementById("${blockName}").innerHTML = 
            '<h4>MCP Response:</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
        })
        .catch(err => {
          document.getElementById("${blockName}").innerHTML = 
            '<div style=\"color:red\">MCP Error: ' + err.message + '</div>';
        });`;
    };

    const mcpJS = Blockly.JavaScript;
    if (mcpJS && mcpJS.forBlock) {
      mcpJS.forBlock[blockName] = generateCode;
    } else {
      Blockly.JavaScript[blockName] = generateCode;
    }
  });
}
