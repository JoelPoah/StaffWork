<template>
  <div class="simple-doc-viewer">
    <div v-if="loading" class="loading-overlay">
      <v-progress-circular indeterminate color="#D5573B" size="64"></v-progress-circular>
      <div class="mt-4">Loading document...</div>
    </div>
    
    <div v-if="documentContent" class="document-content" ref="documentContentRef">
      <div v-html="processedContent"></div>
    </div>
    
    <div v-else-if="!loading" class="empty-state">
      <v-icon size="large" color="#D5573B" class="mb-4">mdi-file-document-outline</v-icon>
      <div>No document loaded</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';

// Props
const props = defineProps({
  documentContent: {
    type: String,
    default: null
  },
  wordErrors: {
    type: Object,
    default: () => ({})
  },
  imageReferences: {
    type: Array,
    default: () => []
  }
});

// Emits
const emit = defineEmits(['error', 'viewer-loaded']);

// State
const documentContentRef = ref(null);
const loading = ref(false);

// Computed properties
const processedContent = computed(() => {
  if (!props.documentContent) return '';
  
  // Return the content as is - we'll apply highlighting after render
  return props.documentContent;
});

// Methods
const applyErrorHighlighting = () => {
  if (!documentContentRef.value || !props.wordErrors) return;
  
  // Reset any previous highlighting
  const allWords = documentContentRef.value.querySelectorAll('.doc-word');
  allWords.forEach(word => {
    word.classList.remove('error-word', 'warning-word');
    word.removeAttribute('data-errors');
  });
  
  // Apply new highlighting
  Object.keys(props.wordErrors).forEach(wordId => {
    const wordElement = documentContentRef.value.querySelector(`#${wordId}`);
    if (wordElement) {
      const wordInfo = props.wordErrors[wordId];
      const hasError = wordInfo.errors.some(err => err.type === 'error');
      const hasWarning = wordInfo.errors.some(err => err.type === 'warning');
      
      if (hasError) {
        wordElement.classList.add('error-word');
      } else if (hasWarning) {
        wordElement.classList.add('warning-word');
      }
      
      // Store error data for tooltips
      wordElement.setAttribute('data-errors', JSON.stringify(wordInfo.errors));
    }
  });
};

const applyImageReferenceHighlighting = () => {
  if (!documentContentRef.value || !props.imageReferences.length) return;
  
  // Reset any previous image reference highlighting
  const allImageRefs = documentContentRef.value.querySelectorAll('.img-ref');
  allImageRefs.forEach(ref => {
    ref.classList.remove('valid-ref', 'invalid-ref');
    ref.removeAttribute('data-ref-info');
  });
  
  // Find all words that are part of image references
  props.imageReferences.forEach(ref => {
    const refId = ref.id;
    const refWords = documentContentRef.value.querySelectorAll(`[data-ref-id="${refId}"]`);
    
    refWords.forEach(wordElement => {
      // Add appropriate class based on reference validity
      if (ref.valid) {
        wordElement.classList.add('valid-ref');
      } else {
        wordElement.classList.add('invalid-ref');
      }
      
      // Store reference data for tooltips
      wordElement.setAttribute('data-ref-info', JSON.stringify(ref));
    });
  });
};

// Watch for changes in document content
watch(() => props.documentContent, (newContent) => {
  if (newContent) {
    loading.value = true;
    
    // Wait for DOM to update, then apply highlighting
    nextTick(() => {
      applyErrorHighlighting();
      applyImageReferenceHighlighting();
      loading.value = false;
      emit('viewer-loaded');
    });
  }
});

// Watch for changes in word errors
watch(() => props.wordErrors, () => {
  nextTick(() => {
    applyErrorHighlighting();
  });
}, { deep: true });

// Watch for changes in image references
watch(() => props.imageReferences, () => {
  nextTick(() => {
    applyImageReferenceHighlighting();
  });
}, { deep: true });

// Initialize on mount if document is available
onMounted(() => {
  if (props.documentContent) {
    loading.value = true;
    
    nextTick(() => {
      applyErrorHighlighting();
      applyImageReferenceHighlighting();
      loading.value = false;
      emit('viewer-loaded');
    });
  }
});
</script>

<style scoped>
.simple-doc-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  background-color: white;
  overflow-y: auto;
  padding: 20px;
  font-family: 'Times New Roman', Times, serif;
  color: #333;
}

.document-content {
  line-height: 1.5;
}

.document-content :deep(p) {
  margin-bottom: 1em;
}

.document-content :deep(h1),
.document-content :deep(h2),
.document-content :deep(h3),
.document-content :deep(h4),
.document-content :deep(h5),
.document-content :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: bold;
}

.document-content :deep(h1) { font-size: 2em; }
.document-content :deep(h2) { font-size: 1.5em; }
.document-content :deep(h3) { font-size: 1.17em; }
.document-content :deep(h4) { font-size: 1em; }
.document-content :deep(h5) { font-size: 0.83em; }
.document-content :deep(h6) { font-size: 0.67em; }

.document-content :deep(ul),
.document-content :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.document-content :deep(li) {
  margin-bottom: 0.5em;
}

.document-content :deep(table) {
  border-collapse: collapse;
  margin-bottom: 1em;
  width: 100%;
}

.document-content :deep(th),
.document-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.document-content :deep(th) {
  background-color: #f2f2f2;
  font-weight: bold;
}

/* Error highlighting */
.document-content :deep(.doc-word) {
  display: inline-block;
  padding: 0 2px;
  border-radius: 2px;
  transition: background-color 0.2s;
}

.document-content :deep(.error-word) {
  background-color: rgba(213, 87, 59, 0.2); /* Jasper with transparency */
  border-bottom: 2px solid #D5573B;
  cursor: help;
}

.document-content :deep(.warning-word) {
  background-color: rgba(119, 125, 167, 0.2); /* Glaucous with transparency */
  border-bottom: 2px dashed #777DA7;
  cursor: help;
}

/* Image reference highlighting */
.document-content :deep(.valid-ref) {
  background-color: rgba(148, 201, 169, 0.2); /* Cambridge blue with transparency */
  border-bottom: 2px solid #94C9A9;
  cursor: help;
}

.document-content :deep(.invalid-ref) {
  background-color: rgba(213, 87, 59, 0.2); /* Jasper with transparency */
  border-bottom: 2px dashed #D5573B;
  cursor: help;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 10;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #777;
  text-align: center;
}
</style>
