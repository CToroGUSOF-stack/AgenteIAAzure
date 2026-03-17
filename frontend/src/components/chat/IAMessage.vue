<template>
  <div class="typing" v-if="props.msg.isLoading">
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
  </div>
  <div v-else class="ia-message-container">
    <div class="ia-message" v-html="formattedText"></div>
    
    <div v-if="uniqueCitations && uniqueCitations.length > 0" class="citations mt-4 border-t pt-2">
      <h4 class="font-bold text-sm mb-2">Referencias:</h4>
      <ul class="list-none p-0">
        <li v-for="citation in uniqueCitations" :key="citation.filename" class="text-sm mb-1">
          <a :href="citation.url" target="_blank" rel="noopener noreferrer" class="citation-link flex items-center gap-2">
            <span class="citation-indices">{{ citation.indices }}</span>
            <span>{{ citation.filename }}</span>
            <span v-if="citation.pages" class="text-gray-500 text-xs">({{ citation.pages }})</span>
          </a>
        </li>
      </ul>
    </div>

    <div class="feedback">
      <button @click="handleCopy()">
        <IconWithTooltip
          :key="isCopied"
          :svg="
            isCopied
              ? `<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' class='bi bi-check' viewBox='0 0 16 16'><path d='M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z'/></svg>`
              : `<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='currentColor' class='bi bi-copy' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1z'/></svg>`
          "
          :size="25"
          tooltip="copiar"
        />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { marked } from "marked";
import IconWithTooltip from "../utils/IconTooltip.vue";

const isCopied = ref(false);

const props = defineProps({
  msg: {
    type: Object,
    required: true,
    rate: { type: [Number, null], default: null },
  },
});

const formattedText = computed(() => {
  if (props.msg.isLoading) return "";
  
  let text = props.msg.text || "";
  
  // Replace [N] patterns with hoverable citation badges before markdown processing
  text = text.replace(/\[(\d+)\]/g, (match, num) => {
    const citationIndex = parseInt(num);
    const citation = props.msg.citations?.find(c => c.index === citationIndex);
    if (citation) {
      // Escape quotes and remove newlines for HTML attribute to prevent markdown parsing issues
      const cleanSnippet = (citation.snippet || '').replace(/[\r\n]+/g, ' ');
      const cleanFilename = (citation.filename || '').replace(/[\r\n]+/g, ' ');
      
      const escapedFilename = cleanFilename.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const escapedSnippet = cleanSnippet.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;').substring(0, 150);
      
      // Debug log for specific citation mapping
      // console.log(`Badge ${citationIndex}: section='${citation.section}', page='${citation.page}'`);

      const locInfo = citation.section ? ` (Sec. ${citation.section})` : (citation.page ? ` (Pág. ${citation.page})` : '');
      const tooltipText = `${escapedFilename}${locInfo}`;
      // Use a placeholder that won't be affected by markdown processing
      return `<span class="citation-badge" data-index="${citationIndex}" data-filename="${escapedFilename}" data-page="${citation.page || ''}" data-snippet="${escapedSnippet}" title="${tooltipText}">[${citationIndex}]</span>`;
    }
    return match; // Keep original if no matching citation
  });
  
  const markdownText = marked(text, {
    breaks: true,
    gfm: true,
  });
  return markdownText;
});

// Deduplicate citations by filename, grouping indices, pages, and sections
const uniqueCitations = computed(() => {
  const citations = props.msg.citations || [];
  if (citations.length > 0) {
    console.log("IAMessage citations:", JSON.parse(JSON.stringify(citations)));
  }
  const grouped = new Map();
  
  for (const citation of citations) {
    const key = citation.filename || citation.url || `citation-${citation.index}`;
    // Log individual citation to check properties
    // console.log("Processing citation:", citation.filename, "Section:", citation.section);
    
    if (grouped.has(key)) {
      const existing = grouped.get(key);
      existing.indexList.push(citation.index);
      if (citation.page && !existing.pageList.includes(citation.page)) {
        existing.pageList.push(citation.page);
      }
      if (citation.section && !existing.sectionList.includes(citation.section)) {
        existing.sectionList.push(citation.section);
      }
    } else {
      grouped.set(key, {
        filename: citation.filename,
        url: citation.url,
        indexList: [citation.index],
        pageList: citation.page ? [citation.page] : [],
        sectionList: citation.section ? [citation.section] : []
      });
    }
  }
  
  return Array.from(grouped.values()).map(item => {
    let locInfo = null;
    if (item.sectionList.length > 0) {
       locInfo = `Sec. ${item.sectionList.join(', ')}`;
    } else if (item.pageList.length > 0) {
       locInfo = `Pág. ${item.pageList.join(', ')}`;
    }

    return {
      filename: item.filename,
      url: item.url,
      indices: item.indexList.map(i => `[${i}]`).join(', '),
      pages: locInfo
    };
  });
});

const handleCopy = async () => {
  await navigator.clipboard.writeText(props.msg.text || "");
  isCopied.value = true;
  setTimeout(() => {
    isCopied.value = false;
  }, 1000);
};
</script>

<style scoped>
.ia-message-container {
  max-width: 75%;
}

.ia-message {
  align-self: flex-start;
  color: #333;
  /* user-select: text; */
  word-wrap: break-word;
}

.ia-message :deep(h1),
.ia-message :deep(h2),
.ia-message :deep(h3),
.ia-message :deep(strong) {
  font-weight: 700;
}
.ia-message:deep(p) {
  margin: 0.5em 0;
}

.ia-message:deep(hr) {
  margin: 1em 0;
}

/* Inline citation badge styles - lighter amber tones */
.ia-message :deep(.citation-badge) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5e6c8 0%, #e8d4a8 100%);
  color: #8b6914;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 8px;
  margin: 0 2px;
  cursor: pointer;
  vertical-align: super;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  border: 1px solid #d4c4a0;
}

.ia-message :deep(.citation-badge:hover) {
  background: linear-gradient(135deg, #e8d4a8 0%, #d9c088 100%);
  transform: scale(1.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  border-color: #c9a227;
}

/* Citation link styles in Referencias section */
.citation-link {
  color: #8b6914;
  text-decoration: none;
  transition: color 0.2s ease;
}

.citation-link:hover {
  color: #6b5210;
  text-decoration: underline;
}

.citation-indices {
  font-family: monospace;
  font-size: 0.75rem;
  background: #f5e6c8;
  color: #8b6914;
  padding: 1px 4px;
  border-radius: 4px;
  border: 1px solid #e8d4a8;
}

.feedback {
  display: flex;
  gap: 2px;
  margin-top: 10px;
}

.feedback button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  color: rgb(63, 60, 60);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: white;
  transition: background-color 0.3s ease;
}

.feedback button:hover {
  background-color: #e0e0e0;
}

.feedback button.voted {
  background-color: #228b2285;
}

.typing {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
}

.dot {
  width: 10px;
  height: 10px;
  margin: 5px 5px;
  background-color: #333;
  border-radius: 50%;
  animation: blink 1.4s infinite both;
}

.dot:nth-child(1) {
  animation-delay: 0.2s;
}

.dot:nth-child(2) {
  animation-delay: 0.4s;
}

.dot:nth-child(3) {
  animation-delay: 0.6s;
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0;
  }

  40% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .ia-message-container {
    max-width: 85%;
  }

  .ia-message {
    font-size: 15px;
  }
}
</style>
