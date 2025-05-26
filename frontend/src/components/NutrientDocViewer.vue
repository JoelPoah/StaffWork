<template>
  <div class="nutrient-container">
    <div v-if="loading" class="loading-overlay">
      <v-progress-circular indeterminate color="#D5573B" size="64"></v-progress-circular>
      <div class="mt-4">Loading document...</div>
    </div>
    <div ref="docContainer" class="doc-container"></div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';

export default {
  name: 'NutrientDocViewer',
  props: {
    documentContent: {
      type: String,
      default: null
    },
    documentBlob: {
      type: Object,
      default: null
    },
    wordErrors: {
      type: Object,
      default: () => ({})
    }
  },
  
  setup(props, { emit }) {
    const docContainer = ref(null);
    const loading = ref(false);
    let instance = null;
    
    // Load Nutrient library dynamically
    const loadNutrient = async () => {
      if (!window.nutrient) {
        try {
          // Import the Nutrient library
          const nutrient = await import('nutrient');
          window.nutrient = nutrient.default || nutrient;
        } catch (error) {
          console.error('Failed to load Nutrient library:', error);
          emit('error', 'Failed to load document viewer library');
          return null;
        }
      }
      return window.nutrient;
    };
    
    // Initialize the document viewer
    const initViewer = async () => {
      if (!props.documentBlob) return;
      
      loading.value = true;
      
      try {
        const nutrient = await loadNutrient();
        if (!nutrient) return;
        
        // Unload any existing instance
        if (instance) {
          await instance.unload();
          instance = null;
        }
        
        // Create a URL for the blob
        const documentUrl = URL.createObjectURL(props.documentBlob);
        
        // Initialize Nutrient with the document
        instance = await nutrient.load({
          container: docContainer.value,
          document: documentUrl,
          baseUrl: '/',
          theme: {
            main: '#777DA7', // Glaucous
            accent: '#D5573B', // Jasper
            background: '#FFFFFF'
          }
        });
        
        // Apply highlighting for errors if available
        if (Object.keys(props.wordErrors).length > 0) {
          applyErrorHighlighting(instance, props.wordErrors);
        }
        
        emit('viewer-loaded', instance);
      } catch (error) {
        console.error('Error initializing document viewer:', error);
        emit('error', 'Failed to initialize document viewer');
      } finally {
        loading.value = false;
      }
    };
    
    // Apply highlighting to words with errors
    const applyErrorHighlighting = (viewerInstance, errors) => {
      if (!viewerInstance || !errors) return;
      
      // This is a placeholder for the actual implementation
      // The exact API will depend on Nutrient's annotation capabilities
      try {
        Object.keys(errors).forEach(wordId => {
          const wordInfo = errors[wordId];
          const hasError = wordInfo.errors.some(err => err.type === 'error');
          const hasWarning = wordInfo.errors.some(err => err.type === 'warning');
          
          // Create annotations based on error type
          if (hasError || hasWarning) {
            const color = hasError ? '#D5573B' : '#777DA7';
            
            // This is pseudocode - actual implementation will use Nutrient's API
            // viewerInstance.createAnnotation({
            //   type: 'highlight',
            //   pageIndex: wordInfo.pageIndex,
            //   rects: wordInfo.rects,
            //   color: color,
            //   note: wordInfo.errors.map(e => e.message).join('\n')
            // });
          }
        });
      } catch (error) {
        console.error('Error applying error highlighting:', error);
      }
    };
    
    // Watch for changes in document blob
    watch(() => props.documentBlob, (newBlob) => {
      if (newBlob) {
        initViewer();
      }
    });
    
    // Cleanup on unmount
    onBeforeUnmount(() => {
      if (instance) {
        instance.unload();
        instance = null;
      }
    });
    
    // Initialize on mount if document is available
    onMounted(() => {
      if (props.documentBlob) {
        initViewer();
      }
    });
    
    return {
      docContainer,
      loading
    };
  }
};
</script>

<style scoped>
.nutrient-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  background-color: white;
}

.doc-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
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
</style>
