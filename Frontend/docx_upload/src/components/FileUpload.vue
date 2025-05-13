<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 100vh;">
    <v-card class="ma-5 pa-5" max-width="600" elevation="12" rounded="lg">
      <v-card-title class="text-center">
        <v-icon large color="primary" class="mr-2">mdi-file-document-outline</v-icon>
        <span class="text-h5 font-weight-bold">DOCX File Upload</span>
      </v-card-title>

      <v-card-text>
        <v-file-input
          v-model="file"
          label="Select .docx file"
          accept=".docx"
          outlined
          prepend-icon="mdi-file-word"
          clearable
          class="mt-5"
          :rules="[v => !!v || 'File is required']"
        ></v-file-input>

        <v-btn 
          color="primary" 
          block 
          size="large" 
          @click="uploadFile" 
          :loading="loading"
          :disabled="!file"
          class="mt-2"
          rounded="lg"
        >
          <template v-slot:loader>
            <v-progress-circular indeterminate color="white"></v-progress-circular>
          </template>
          <v-icon left>mdi-cloud-upload</v-icon>
          Upload
        </v-btn>

        <v-expand-transition>
          <div v-if="messages.length > 0" class="mt-5">
            <v-alert
              v-for="(msg, idx) in messages"
              :key="idx"
              :type="getAlertType(msg)"
              class="mb-3"
              variant="tonal"
              :icon="getAlertIcon(msg)"
              border="start"
              :border-color="getAlertColor(msg)"
            >
              <template v-slot:title>
                {{ getAlertTitle(msg) }}
              </template>
              {{ msg }}
            </v-alert>

            <v-divider class="my-3"></v-divider>
            
            <div class="text-center">
              <v-btn 
                v-if="hasSuccess"
                color="success" 
                variant="outlined" 
                class="mt-2"
                rounded="lg"
              >
                <v-icon left>mdi-check</v-icon>
                Continue
              </v-btn>
              <v-btn 
                v-else
                color="primary" 
                variant="text" 
                class="mt-2"
                @click="file = null; messages = []"
                rounded="lg"
              >
                <v-icon left>mdi-reload</v-icon>
                Try Again
              </v-btn>
            </div>
          </div>
        </v-expand-transition>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';

const file = ref(null);
const messages = ref([]);
const loading = ref(false);

const hasSuccess = computed(() => {
  return messages.value.some(msg => getAlertType(msg) === 'success');
});

const uploadFile = async () => {
  if (!file.value) {
    messages.value = ['Please select a file first'];
    return;
  }

  const formData = new FormData();
  formData.append('file', file.value);

  loading.value = true;
  messages.value = [];

  try {
    const response = await axios.post('http://localhost:5000/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    messages.value = response.data.errors || [];
  } catch (err) {
    if (err.response && err.response.data) {
      messages.value = err.response.data.errors || ['An error occurred'];
    } else {
      messages.value = ['Upload failed. Please check your server.'];
    }
  } finally {
    loading.value = false;
  }
};

// Helpers
const getAlertType = (msg) => {
  if (msg.toLowerCase().includes('complete')) return 'success';
  if (msg.toLowerCase().includes('not') || msg.toLowerCase().includes('fail')) return 'error';
  return 'warning';
};

const getAlertIcon = (msg) => {
  if (msg.toLowerCase().includes('complete')) return 'mdi-check-circle-outline';
  if (msg.toLowerCase().includes('not') || msg.toLowerCase().includes('fail')) return 'mdi-alert-circle-outline';
  return 'mdi-information-outline';
};

const getAlertColor = (msg) => {
  const type = getAlertType(msg);
  return type === 'success' ? 'success' : type === 'error' ? 'error' : 'warning';
};

const getAlertTitle = (msg) => {
  if (msg.toLowerCase().includes('complete')) return 'Success!';
  if (msg.toLowerCase().includes('not') || msg.toLowerCase().includes('fail')) return 'Error';
  return 'Notice';
};
</script>

<style scoped>
.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  transform: translateY(-2px);
}

.v-btn {
  letter-spacing: 0.5px;
  text-transform: none;
  font-weight: 600;
}
</style>