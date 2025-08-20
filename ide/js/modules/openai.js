// OpenAI module block generator
// Exports: generateOpenAIBlocks(spec)

export function generateOpenAIBlocks(spec) {
  // Add OpenAI category with safety checks
  let openaiCategory = document.getElementById('openaiCategory');
  if (!openaiCategory) {
    openaiCategory = document.createElement('category');
    openaiCategory.id = 'openaiCategory';
    openaiCategory.setAttribute('name', 'OpenAI');
    openaiCategory.setAttribute('colour', '300');

    const toolbox = document.getElementById('toolbox');
    if (toolbox) {
      toolbox.appendChild(openaiCategory);
    } else {
      console.warn('Toolbox element not found for OpenAI category');
      return;
    }
  }

  // Clear existing blocks to prevent conflicts
  try {
    openaiCategory.innerHTML = '';
  } catch (e) {
    console.warn('Could not clear OpenAI category:', e);
  }

  Object.entries(spec.blocks || {}).forEach(([blockId, blockSpec]) => {
    const blockName = `openai_${blockId}`;

    const blockEl = document.createElement('block');
    blockEl.setAttribute('type', blockName);
    openaiCategory.appendChild(blockEl);

    Blockly.Blocks[blockName] = {
      init: function () {
        this.appendDummyInput().appendField(`🤖 ${blockSpec.summary}`);

        if (blockSpec.params) {
          blockSpec.params.forEach((param) => {
            this.appendValueInput(param.name.toUpperCase())
              .appendField(`${param.name}:`)
              .setCheck(['String', 'Number']);
          });
        }

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(300);
      },
    };

    const generateCode = function (block, generator) {
      return `
        htmlOutput += '<div id="${blockName}">Processing with AI...</div>';
        // Note: Replace YOUR_OPENAI_KEY with actual API key
        fetch("${spec.base_url}${blockSpec.path}", {
          method: "${blockSpec.method}",
          headers: {
            'Authorization': 'Bearer YOUR_OPENAI_KEY',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: "gpt-3.5-turbo",
            messages: [{"role": "user", "content": "Hello from Blockly!"}],
            max_tokens: 100
          })
        })
        .then(r => r.json())
        .then(data => {
          document.getElementById("${blockName}").innerHTML = 
            '<h4>AI Response:</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
        })
        .catch(err => {
          document.getElementById("${blockName}").innerHTML = 
            '<div style="color:red">OpenAI API Error: ' + err.message + '</div>';
        });`;
    };

    const openaiJS = Blockly.JavaScript;
    if (openaiJS && openaiJS.forBlock) {
      openaiJS.forBlock[blockName] = generateCode;
    } else {
      Blockly.JavaScript[blockName] = generateCode;
    }
  });
}
