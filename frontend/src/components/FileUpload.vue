<template>
  <v-card class="ma-4 pa-4 file-upload-card" elevation="2">
    <h3 class="text-h6 mb-4 d-flex align-center">
      <v-icon class="mr-2" color="#D5573B">mdi-upload</v-icon>
      Upload Document
    </h3>
    
    <v-file-input
      v-model="file"
      accept=".docx"
      label="Select a DOCX file"
      prepend-icon="mdi-file-document"
      show-size
      truncate-length="25"
      :loading="loading"
      :disabled="loading"
      variant="outlined"
      color="#885053"
      @change="handleFileChange"
      class="mb-4"
    ></v-file-input>
    
    <v-btn
      block
      color="#D5573B"
      :loading="loading"
      :disabled="!file || loading"
      @click="uploadFile"
      class="mb-2"
    >
      <v-icon left>mdi-check</v-icon>
      Validate Document
    </v-btn>
    
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="mt-4"
      density="compact"
    >
      {{ error }}
    </v-alert>
  </v-card>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

// State
const file = ref(null);
const loading = ref(false);
const error = ref(null);

// API URL - update with deployed backend URL
const API_URL = import.meta.env.VITE_API_URL;

// Emits
const emit = defineEmits([
  'document-loaded', 
  'errors-received', 
  'word-errors-received',
  'images-received',
  'image-references-received',
  'file-selected'
]);

// Methods
const handleFileChange = () => {
  error.value = null;
  
  // Emit the file for document viewer
  if (file.value) {
    emit('file-selected', file.value);
  } else {
    emit('file-selected', null);
  }
};

const uploadFile = async () => {
  if (!file.value) return;
  
  loading.value = true;
  error.value = null;
  
  try {
    const formData = new FormData();
    formData.append('file', file.value);
    
    console.log('Sending request to:', API_URL);
    const response = await axios.post(`${API_URL}/validate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    console.log('Response received:', response.data);
    
    // Process response
    if (response.data) {

      // Emit document content
      emit('document-loaded', response.data.content);

      const errorsString = JSON.stringify(response.data.errors.summary, null, 2); // pretty print
      const analysisPrompt = `Give an analysis of the following document and be critical about its consistency and whether it has a good thought process flow to it. These are the errors: ${errorsString}`;
      try {
        const chatResponse = await axios.post(`${import.meta.env.VITE_LLM_API_URL}`, {
          message: analysisPrompt,
          documentContent: response.data.content
        });
      
        if (chatResponse.data?.response) {
          // Emit to ChatInterface so it can add the message
          emit('message-sent', analysisPrompt); // optional if you want user input shown

          emit('analysis-response', String(chatResponse.data.response));
        }
      } catch (chatError) {
        console.error('Error getting analysis from LLM:', chatError);
      }
      
      // Emit validation errors
      emit('errors-received', response.data.errors || {
        summary: [],
        formatting: [],
        fonts: [],
        images: []
      });
      
      // Emit word-level errors for highlighting
      emit('word-errors-received', response.data.word_errors || {});
      
      // Emit images and image references
      emit('images-received', response.data.images || []);
      emit('image-references-received', response.data.image_references || []);
    } else {
      error.value = 'Invalid response from server';
    }
  } catch (err) {
    console.error('Error uploading file:', err);
    error.value = err.response?.data?.message || 'Error uploading file. Please try again.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.file-upload-card {
  background-color: white;
  border-left: 4px solid #D5573B;
}
</style>
