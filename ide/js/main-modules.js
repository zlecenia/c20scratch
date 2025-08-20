// Bridge module: import generators and expose globally for existing inline code
import { generateLinkedInBlocks } from './modules/linkedin.js';
import { generateOpenAIBlocks } from './modules/openai.js';
import { generateMCPBlocks } from './modules/mcp.js';

// Expose to global scope so non-module scripts can call them
window.generateLinkedInBlocks = generateLinkedInBlocks;
window.generateOpenAIBlocks = generateOpenAIBlocks;
window.generateMCPBlocks = generateMCPBlocks;
// Also expose under a dedicated namespace to avoid name collisions with inline functions
window.ModuleGenerators = {
  generateLinkedInBlocks,
  generateOpenAIBlocks,
  generateMCPBlocks,
};
