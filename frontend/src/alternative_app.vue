<template>
  <v-app>
    <v-main class="main-background">
      <v-container fluid class="pa-0 fill-height">
        <v-row no-gutters class="fill-height">
          <!-- Left side: Document upload and viewer -->
          <v-col cols="12" md="6" class="left-panel">
            <v-sheet class="fill-height pa-4" color="#C6ECAE">
              <h2 class="text-h5 mb-4 d-flex align-center text-secondary">
                <v-icon class="mr-2" color="#D5573B">mdi-file-document-outline</v-icon>
                Document Viewer
              </h2>

              <!-- FileUpload component emits various events -->
              <FileUpload
                @analysis-response="handleAnalysis"
                @document-loaded="handleDocumentLoaded"
                @errors-received="handleErrors"
                @word-errors-received="handleWordErrors"
                @images-received="handleImages"
                @image-references-received="handleImageReferences"
                @file-selected="handleFileSelected"
              />

              <!-- Document viewer placeholder -->
              <v-sheet v-if="documentLoaded" class="doc-preview mt-4 pa-4" rounded elevation="1" color="white">
                <PDFViewer />
                <div v-if="!documentContent" class="text-center py-8 text-medium-emphasis">
                  No document loaded
                </div>
              </v-sheet>

              <!-- Error summary can be added here as needed -->
            </v-sheet>
          </v-col>

          <!-- Right side: Chat Interface -->
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
  </v-app>
</template>

<script setup>
import { ref } from 'vue';
import FileUpload from './components/FileUpload.vue';
import ChatInterface from './components/ChatInterface.vue';
import PDFViewer from './components/PDFViewer.vue';

// Reactive state for document content and errors
const documentContent = ref(null);
const documentLoaded = ref(false);
const errors = ref({
  summary: [],
  formatting: [],
  fonts: [],
  images: []
});

// Reference to ChatInterface child component
const chatInterfaceRef = ref(null);

// When analysis response comes from FileUpload
const handleAnalysis = (analysisText) => {
  alert('[App.vue] Analysis received: ' + analysisText);

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

// Handlers for FileUpload emitted events
const handleDocumentLoaded = (content) => {
  documentContent.value = content;
  documentLoaded.value = !!content;
};

const handleErrors = (errorData) => {
  errors.value = errorData || {
    summary: [],
    formatting: [],
    fonts: [],
    images: []
  };
};

const handleWordErrors = (wordErrorData) => {
  // Optional: handle word errors if needed
};

const handleImages = (imagesData) => {
  // Optional: handle images if needed
};

const handleImageReferences = (imageReferencesData) => {
  // Optional: handle image references if needed
};

const handleFileSelected = (file) => {
  // Reset states when new file is selected
  documentContent.value = null;
  documentLoaded.value = false;
  errors.value = {
    summary: [],
    formatting: [],
    fonts: [],
    images: []
  };
};

// Optional: handle messages sent from ChatInterface
const handleMessageSent = (message) => {
  console.log('User sent message:', message);
};
</script>

<style>
.main-background {
  background-color: #94C9A9;
}
.left-panel, .right-panel {
  height: 100vh;
  overflow-y: auto;
}
.left-panel {
  background-color: #C6ECAE;
}
.right-panel {
  background-color: #777DA7;
}
.doc-preview {
  background-color: white;
  min-height: 400px;
  max-height: 60vh;
  overflow-y: auto;
  color: #333;
  font-family: 'Times New Roman', Times, serif;
  border-left: 4px solid #D5573B;
}
</style>
