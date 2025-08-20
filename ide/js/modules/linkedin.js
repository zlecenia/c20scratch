// LinkedIn module block generator
// Exports: generateLinkedInBlocks(spec)

export function generateLinkedInBlocks(spec) {
  // Add LinkedIn category if not exists - with safety checks
  let linkedinCategory = document.getElementById('linkedinCategory');
  if (!linkedinCategory) {
    linkedinCategory = document.createElement('category');
    linkedinCategory.id = 'linkedinCategory';
    linkedinCategory.setAttribute('name', 'LinkedIn');
    linkedinCategory.setAttribute('colour', '0');

    const toolbox = document.getElementById('toolbox');
    if (toolbox) {
      toolbox.appendChild(linkedinCategory);
    } else {
      console.warn('Toolbox element not found for LinkedIn category');
      return;
    }
  }

  // Clear existing blocks to prevent conflicts
  try {
    linkedinCategory.innerHTML = '';
  } catch (e) {
    console.warn('Could not clear LinkedIn category:', e);
  }

  Object.entries(spec.blocks || {}).forEach(([blockId, blockSpec]) => {
    const blockName = `linkedin_${blockId}`;

    // Add block to toolbox
    const blockEl = document.createElement('block');
    blockEl.setAttribute('type', blockName);
    linkedinCategory.appendChild(blockEl);

    // Define block
    Blockly.Blocks[blockName] = {
      init: function () {
        this.appendDummyInput().appendField(`📊 ${blockSpec.summary}`);

        // Add parameter inputs
        if (blockSpec.params) {
          blockSpec.params.forEach((param) => {
            this.appendValueInput(param.name.toUpperCase())
              .appendField(`${param.name}:`)
              .setCheck(['String', 'Number']);
          });
        }

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(0);
      },
    };

    // Generate code
    const blocklyJS = Blockly.JavaScript;
    const generateCode = function (block, generator) {
      let url = `"${spec.base_url}${blockSpec.path}"`;

      // Handle path params
      if (blockSpec.params) {
        blockSpec.params.forEach((param) => {
          const value = generator
            ? generator.valueToCode(block, param.name.toUpperCase(), generator.ORDER_NONE)
            : Blockly.JavaScript.valueToCode(block, param.name.toUpperCase(), Blockly.JavaScript.ORDER_NONE);
          if (value) {
            url = url.replace(`{${param.name}}`, '" + ' + value + ' + "');
          }
        });
      }

      return `
          htmlOutput += '<div id="${blockName}">Loading LinkedIn data...</div>';
          fetch(${url}, {
              headers: {
                  'Authorization': 'Bearer YOUR_LINKEDIN_TOKEN'
              }
          })
          .then(r => r.json())
          .then(data => {
              document.getElementById("${blockName}").innerHTML = 
                  '<h4>LinkedIn Data:</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
          })
          .catch(err => {
              document.getElementById("${blockName}").innerHTML = 
                  '<div style="color:red">LinkedIn API Error: ' + err.message + '</div>';
          });
      `;
    };

    if (blocklyJS && blocklyJS.forBlock) {
      blocklyJS.forBlock[blockName] = generateCode;
    } else {
      Blockly.JavaScript[blockName] = generateCode;
    }
  });
}
