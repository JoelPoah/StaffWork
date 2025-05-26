<template>
  <v-sheet class="fill-height d-flex flex-column chat-interface" color="#777DA7">
    <div class="chat-header pa-4">
      <h2 class="text-h5 text-white d-flex align-center">
        <v-icon class="mr-2" color="white">mdi-chat-processing</v-icon>
        Document Assistant
      </h2>
    </div>
    
    <div class="chat-messages pa-4 flex-grow-1" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="mb-4">
        <div :class="['message-bubble', message.sender === 'user' ? 'user-message' : 'assistant-message']">
          <div class="message-content">{{ message.text }}</div>
        </div>
      </div>
      <div v-if="loading" class="typing-indicator">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>
    
    <div class="chat-input pa-4">
      <v-form @submit.prevent="sendMessage">
        <v-text-field
          v-model="userInput"
          placeholder="Ask about your document..."
          variant="outlined"
          color="white"
          bg-color="rgba(255, 255, 255, 0.1)"
          hide-details
          :disabled="!documentLoaded || loading"
          :loading="loading"
          append-inner-icon="mdi-send"
          @click:append-inner="sendMessage"
          class="chat-input-field"
        ></v-text-field>
      </v-form>
      
      <div class="text-caption text-white-darken-2 mt-2">
        <v-icon size="small" color="white" class="mr-1">mdi-information-outline</v-icon>
        {{ documentLoaded ? 'Ask questions about your document or formatting issues' : 'Upload a document to start chatting' }}
      </div>
    </div>
    
    <div class="chat-footer pa-2 d-flex justify-end">
      <span class="text-caption text-white-darken-2">Made with Manus</span>
    </div>
  </v-sheet>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';

// Props
const props = defineProps({
  documentLoaded: {
    type: Boolean,
    default: false
  },
  documentErrors: {
    type: Object,
    default: () => ({})
  },
  documentContent: {
    type: String,
    default: ''
  }
});

// Emits
const emit = defineEmits(['message-sent']);

// State
const userInput = ref('');
const messages = ref([]);
const loading = ref(false);
const messagesContainer = ref(null);

// API URL - update with deployed backend URL for the RAG LLM server
const API_URL = 'https://rogh5izc991v.manus.space'; // Main backend URL
const LLM_API_URL = 'https://rogh5izc991v.manus.space/chat'; // LLM chat endpoint

// Methods
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return;
  
  const userMessage = userInput.value.trim();
  
  // Add user message to chat
  messages.value.push({
    sender: 'user',
    text: userMessage
  });
  
  // Clear input
  userInput.value = '';
  
  // Scroll to bottom
  await nextTick();
  scrollToBottom();
  
  // Show loading indicator
  loading.value = true;
  
  try {
    // Send message to LLM backend
    const response = await axios.post(LLM_API_URL, {
      message: userMessage,
      documentContent: props.documentContent
    });
    
    // Add assistant response
    if (response.data && response.data.response) {
      messages.value.push({
        sender: 'assistant',
        text: response.data.response
      });
    } else {
      // Fallback response if API fails
      messages.value.push({
        sender: 'assistant',
        text: "I'm sorry, I couldn't process your request. Please try again later."
      });
    }
    
    // Emit event
    emit('message-sent', userMessage);
  } catch (error) {
    console.error('Error sending message:', error);
    
    // Add error message with more helpful information
    let errorMessage = "I'm sorry, I couldn't process your request.";
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      if (error.response.status === 500) {
        errorMessage += " The server encountered an internal error. Please try again later.";
      } else if (error.response.status === 400) {
        errorMessage += " Please ensure your question is clear and try again.";
      } else if (error.response.status === 404) {
        errorMessage += " The chat service is currently unavailable. Please try again later.";
      }
    } else if (error.request) {
      // The request was made but no response was received
      errorMessage += " No response received from the server. Please check your connection and try again.";
    } else {
      // Something happened in setting up the request that triggered an Error
      errorMessage += " An unexpected error occurred. Please try again.";
    }
    
    messages.value.push({
      sender: 'assistant',
      text: errorMessage
    });
  } finally {
    loading.value = false;
    
    // Scroll to bottom after response
    await nextTick();
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const addWelcomeMessage = () => {
  // Clear existing messages
  messages.value = [];
  
  // Add welcome message
  messages.value.push({
    sender: 'assistant',
    text: 'Your document has been uploaded. How can I help you with it today? You can ask me to analyze the document, check for grammar issues, or suggest vocabulary improvements.'
  });
  
  // If there are errors, add a message about them
  if (props.documentErrors && 
      props.documentErrors.summary && 
      props.documentErrors.summary.length > 0) {
    
    const errorCount = props.documentErrors.summary.find(s => s.message && s.message.includes('Found'));
    
    if (errorCount) {
      messages.value.push({
        sender: 'assistant',
        text: `I've detected some formatting issues in your document. ${errorCount.message} Words with errors are highlighted - hover over them to see details.`
      });
    }
  }
  
  // Scroll to bottom
  nextTick(scrollToBottom);
};

// Watch for document loaded changes
watch(() => props.documentLoaded, (newVal) => {
  if (newVal) {
    addWelcomeMessage();
  }
});

// Lifecycle hooks
onMounted(() => {
  // Add initial message
  if (messages.value.length === 0) {
    messages.value.push({
      sender: 'assistant',
      text: 'Hello! Please upload a document to get started. I can help you analyze the document, check for grammar issues, and suggest improvements.'
    });
  }
});

// Expose methods to parent component
defineExpose({
  addWelcomeMessage
});
</script>

<style scoped>
.chat-interface {
  position: relative;
  border-radius: 0;
}

.chat-header {
  background-color: #885053; /* Rose taupe */
}

.chat-messages {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  margin-bottom: 8px;
  position: relative;
  word-break: break-word;
}

.user-message {
  align-self: flex-end;
  background-color: #D5573B; /* Jasper */
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.assistant-message {
  align-self: flex-start;
  background-color: #C6ECAE; /* Tea green */
  color: #333;
  margin-right: auto;
  border-bottom-left-radius: 4px;
}

.message-content {
  line-height: 1.4;
  white-space: pre-line; /* Preserve line breaks in responses */
}

.chat-input {
  background-color: rgba(0, 0, 0, 0.1);
}

.chat-input-field {
  border-radius: 24px;
}

.chat-footer {
  background-color: rgba(0, 0, 0, 0.2);
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #C6ECAE;
  border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.5s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}
</style>
