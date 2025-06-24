<template>
  <v-app>
    <v-main class="main-background">
      <v-container fluid class="pa-0 fill-height">
        <v-row no-gutters class="fill-height">
          <!-- Left side: Document visualization and error display -->
          <v-col cols="12" md="6" class="left-panel">
            <v-sheet class="fill-height pa-4" color="#C6ECAE">
              <h2 class="text-h5 mb-4 d-flex align-center text-secondary">
                <v-icon class="mr-2" color="#D5573B">mdi-file-document-outline</v-icon>
                Document Viewer
              </h2>
              
              <!-- Document upload component -->
              <FileUpload 
                @document-loaded="handleDocumentLoaded" 
                @errors-received="handleErrors" 
                @word-errors-received="handleWordErrors"
                @images-received="handleImages"
                @image-references-received="handleImageReferences"
                @file-selected="handleFileSelected"
                @analysis-response="handleAnalysis"
              />
              
              <!-- Document visualization area using SimpleDocViewer -->
              <v-sheet v-if="documentLoaded" class="doc-preview mt-4 pa-4" rounded elevation="1" color="white">
                <!-- Use SimpleDocViewer for document display -->
                <!-- <SimpleDocViewer
                  :document-content="documentContent"
                  :word-errors="wordErrors"
                  :image-references="imageReferences"
                  @viewer-loaded="handleViewerLoaded"
                  @error="handleViewerError"
                  class="simple-viewer"
                /> -->
                <PDFViewer/>
                
                <!-- Empty state -->
                <div v-if="!documentContent" class="text-center py-8 text-medium-emphasis">
                  No document loaded
                </div>
              </v-sheet>
              
              <!-- Error summary -->
              <v-expand-transition>
                <div v-if="hasErrors" class="mt-4">
                  <h3 class="text-subtitle-1 font-weight-bold mb-2 text-secondary">
                    <v-icon color="#D5573B" class="mr-1">mdi-alert-circle</v-icon>
                    Document Issues
                  </h3>
                  
                  <!-- Summary section -->
                  <div v-if="errors.summary && errors.summary.length > 0">
                    <v-alert
                      v-for="(error, idx) in errors.summary"
                      :key="'summary-' + idx"
                      :type="error.type || 'warning'"
                      class="mb-2"
                      variant="tonal"
                      density="compact"
                      border="start"
                    >
                      {{ error.message }}
                    </v-alert>
                  </div>
                  
                  <!-- Formatting errors -->
                  <div v-if="errors.formatting && errors.formatting.length > 0">
                    <v-alert
                      type="warning"
                      class="mb-2"
                      variant="tonal"
                      density="compact"
                      border="start"
                      color="#777DA7"
                    >
                      Found {{ errors.formatting.length }} formatting issues
                    </v-alert>
                  </div>
                  
                  <!-- Font errors -->
                  <div v-if="errors.fonts && errors.fonts.length > 0">
                    <v-alert
                      type="error"
                      class="mb-2"
                      variant="tonal"
                      density="compact"
                      border="start"
                      color="#D5573B"
                    >
                      Found {{ errors.fonts.length }} font issues
                    </v-alert>
                  </div>
                  
                  <!-- Image reference issues -->
                  <div v-if="errors.images && errors.images.length > 0">
                    <v-alert
                      v-for="(error, idx) in errors.images"
                      :key="'image-' + idx"
                      :type="error.type || 'warning'"
                      class="mb-2"
                      variant="tonal"
                      density="compact"
                      border="start"
                      color="#777DA7"
                    >
                      {{ error.message }}
                    </v-alert>
                  </div>
                  
                  <!-- Instruction for users -->
                  <v-alert
                    type="info"
                    class="mt-2"
                    variant="tonal"
                    density="compact"
                    border="start"
                    color="#94C9A9"
                  >
                    <ul class="mb-0 ps-4">
                      <li>Hover over highlighted words to see specific formatting errors</li>
                      <li v-if="hasImageReferences">Image references are highlighted - valid references in green, missing references in orange</li>
                    </ul>
                  </v-alert>
                </div>
              </v-expand-transition>
            </v-sheet>
          </v-col>
          
          <!-- Right side: Chatbot interface -->
          <v-col cols="12" md="6" class="right-panel">
            <ChatInterface 
              ref="chatInterfaceRef"
              :document-loaded="documentLoaded"
              :document-errors="errors"
              :document-content="documentContent"
              @message-sent="handleMessageSent"
            />
          </v-col>
        </v-row>
      </v-container>
    </v-main>
    
    <!-- Tooltip for word errors -->
    <v-tooltip
      v-model="showTooltip"
      :activator="tooltipActivator"
      location="top"
      content-class="error-tooltip"
    >
      <div v-for="(error, idx) in currentWordErrors" :key="idx" class="tooltip-error">
        <v-icon :color="error.type === 'error' ? '#D5573B' : '#777DA7'" size="small" class="mr-1">
          {{ error.type === 'error' ? 'mdi-alert-circle' : 'mdi-alert' }}
        </v-icon>
        {{ error.message }}
      </div>
    </v-tooltip>
    
    <!-- Tooltip for image references -->
    <v-tooltip
      v-model="showImageRefTooltip"
      :activator="imageRefTooltipActivator"
      location="top"
      content-class="image-ref-tooltip"
    >
      <div class="tooltip-image-ref">
        <v-icon :color="currentImageRef.valid ? '#94C9A9' : '#D5573B'" size="small" class="mr-1">
          {{ currentImageRef.valid ? 'mdi-check-circle' : 'mdi-alert-circle' }}
        </v-icon>
        {{ currentImageRef.valid ? 'Valid image reference' : 'Missing image reference' }}
      </div>
    </v-tooltip>
  </v-app>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import FileUpload from './components/FileUpload.vue';
import ChatInterface from './components/ChatInterface.vue';
import SimpleDocViewer from './components/SimpleDocViewer.vue';
import PDFViewer from './components/PDFViewer.vue'


// Document state
const documentContent = ref(null);
const errors = ref({
  summary: [],
  formatting: [],
  fonts: [],
  images: []
});
const wordErrors = ref({});
const images = ref([]);
const imageReferences = ref([]);

// Tooltip state for word errors
const showTooltip = ref(false);
const tooltipActivator = ref(null);
const currentWordErrors = ref([]);

// Tooltip state for image references
const showImageRefTooltip = ref(false);
const imageRefTooltipActivator = ref(null);
const currentImageRef = ref({});

// Computed properties
const documentLoaded = computed(() => !!documentContent.value);
const hasErrors = computed(() => {
  return (
    (errors.value.summary && errors.value.summary.length > 0) ||
    (errors.value.formatting && errors.value.formatting.length > 0) ||
    (errors.value.fonts && errors.value.fonts.length > 0) ||
    (errors.value.images && errors.value.images.length > 0)
  );
});
const hasImageReferences = computed(() => imageReferences.value.length > 0);

// Event handlers
const handleFileSelected = (file) => {
  // Reset state when a new file is selected
  documentContent.value = null;
  errors.value = {
    summary: [],
    formatting: [],
    fonts: [],
    images: []
  };
  wordErrors.value = {};
  images.value = [];
  imageReferences.value = [];
};

const handleDocumentLoaded = (content) => {
  console.log('Document loaded with content length:', content ? content.length : 0);
  documentContent.value = content;
};

const handleAnalysis = (analysisText) => {

  const chatComponent = chatInterfaceRef.value;
  if (!chatComponent) {
    console.warn('ChatInterface ref is not ready');
    return;
  }

  // Use the exposed method in ChatInterface to set messages reactively
  chatComponent.setMessages([
    {
      sender: 'assistant',
      text: 'Your document has been uploaded. How can I help you with it today?'
    },
    {
      sender: 'assistant',
      text: analysisText
    }
  ]);
};



const handleViewerLoaded = () => {
  console.log('Document viewer loaded successfully');
  
  // Setup event listeners for tooltips
  setupTooltipEventListeners();
};

const handleViewerError = (error) => {
  console.error('Document viewer error:', error);
  
  // Add error to summary
  errors.value.summary = [
    ...(errors.value.summary || []),
    {
      type: 'error',
      message: `Error displaying document: ${error}`
    }
  ];
};

const handleErrors = (errorData) => {
  console.log('Received errors:', errorData);
  errors.value = errorData || {
    summary: [],
    formatting: [],
    fonts: [],
    images: []
  };
};

const handleWordErrors = (wordErrorData) => {
  console.log('Received word errors:', wordErrorData);
  wordErrors.value = wordErrorData || {};
};

const handleImages = (imagesData) => {
  console.log('Received images:', imagesData);
  images.value = imagesData || [];
};

const handleImageReferences = (imageReferencesData) => {
  console.log('Received image references:', imageReferencesData);
  imageReferences.value = imageReferencesData || [];
};

const handleMessageSent = (message) => {
  console.log('Message sent:', message);
};

// Setup tooltip event listeners
const setupTooltipEventListeners = () => {
  nextTick(() => {
    // Find all document elements
    const docContainer = document.querySelector('.simple-viewer');
    if (!docContainer) return;
    
    // Add event listeners for word errors
    const errorWords = docContainer.querySelectorAll('.error-word, .warning-word');
    errorWords.forEach(word => {
      word.addEventListener('mouseenter', handleWordMouseEnter);
      word.addEventListener('mouseleave', hideWordTooltip);
    });
    
    // Add event listeners for image references
    const imageRefs = docContainer.querySelectorAll('.valid-ref, .invalid-ref');
    imageRefs.forEach(ref => {
      ref.addEventListener('mouseenter', handleImageRefMouseEnter);
      ref.addEventListener('mouseleave', hideImageRefTooltip);
    });
  });
};

// Tooltip handlers for word errors
const handleWordMouseEnter = (event) => {
  const wordId = event.target.id;
  if (wordErrors.value[wordId]) {
    currentWordErrors.value = wordErrors.value[wordId].errors;
    tooltipActivator.value = event.target;
    showTooltip.value = true;
  }
};

const hideWordTooltip = () => {
  showTooltip.value = false;
  currentWordErrors.value = [];
};

// Tooltip handlers for image references
const handleImageRefMouseEnter = (event) => {
  const refId = event.target.getAttribute('data-ref-id');
  const ref = imageReferences.value.find(r => r.id === refId);
  if (ref) {
    currentImageRef.value = ref;
    imageRefTooltipActivator.value = event.target;
    showImageRefTooltip.value = true;
  }
};

const hideImageRefTooltip = () => {
  showImageRefTooltip.value = false;
  currentImageRef.value = {};
};

// Reference to chat interface component
const chatInterfaceRef = ref(null);

// Debug watcher
watch(errors, (newVal) => {
  console.log('Errors updated:', newVal);
}, { deep: true });

// Watch for document content changes
watch(documentContent, () => {
  nextTick(() => {
    setupTooltipEventListeners();
  });
});

// Initialize
onMounted(() => {
  // Setup global event listener for dynamic content
  document.addEventListener('DOMContentLoaded', () => {
    setupTooltipEventListeners();
  });
});
</script>

<style>
.main-background {
  background-color: #94C9A9; /* Cambridge blue as background */
}

.left-panel, .right-panel {
  height: 100vh;
  overflow-y: auto;
}

.left-panel {
  background-color: #C6ECAE; /* Tea green */
}

.right-panel {
  background-color: #777DA7; /* Glaucous */
}

.doc-preview {
  background-color: white;
  min-height: 400px;
  max-height: 60vh;
  overflow-y: auto;
  color: #333;
  font-family: 'Times New Roman', Times, serif;
  border-left: 4px solid #D5573B; /* Jasper accent */
}

.simple-viewer {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.error-tooltip, .image-ref-tooltip {
  max-width: 300px;
  padding: 8px;
  background-color: #333 !important;
}

.tooltip-error, .tooltip-image-ref {
  margin-bottom: 4px;
  color: white;
  font-size: 14px;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .left-panel, .right-panel {
    height: auto;
    min-height: 50vh;
  }
  
  .doc-preview {
    min-height: 300px;
    max-height: 50vh;
  }
  
  .simple-viewer {
    min-height: 300px;
  }
}
</style>
