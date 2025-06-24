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
  documentLoaded: Boolean,
  documentErrors: Object,
  documentContent: String
});

// Emits
const emit = defineEmits(['message-sent']);

// State
const userInput = ref('');
const messages = ref([]);
const loading = ref(false);
const messagesContainer = ref(null);

// API URLs (update as needed)
const API_URL = import.meta.env.VITE_API_URL;
const LLM_API_URL = import.meta.env.VITE_LLM_API_URL;

// Methods
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return;
  
  const userMessage = userInput.value.trim();
  
  messages.value.push({
    sender: 'user',
    text: userMessage
  });
  
  userInput.value = '';
  
  await nextTick();
  scrollToBottom();
  
  loading.value = true;
  
  try {
    const response = await axios.post(LLM_API_URL, {
      message: userMessage,
      documentContent: props.documentContent
    });
    
    if (response.data && response.data.response) {
      messages.value.push({
        sender: 'assistant',
        text: response.data.response
      });
    } else {
      messages.value.push({
        sender: 'assistant',
        text: "I'm sorry, I couldn't process your request. Please try again later."
      });
    }
    
    emit('message-sent', userMessage);
  } catch (error) {
    console.error('Error sending message:', error);
    
    let errorMessage = "I'm sorry, I couldn't process your request.";
    if (error.response) {
      if (error.response.status === 500) {
        errorMessage += " The server encountered an internal error. Please try again later.";
      } else if (error.response.status === 400) {
        errorMessage += " Please ensure your question is clear and try again.";
      } else if (error.response.status === 404) {
        errorMessage += " The chat service is currently unavailable. Please try again later.";
      }
    } else if (error.request) {
      errorMessage += " No response received from the server. Please check your connection and try again.";
    } else {
      errorMessage += " An unexpected error occurred. Please try again.";
    }
    
    messages.value.push({
      sender: 'assistant',
      text: errorMessage
    });
  } finally {
    loading.value = false;
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
  messages.value = [];
  messages.value.push({
    sender: 'assistant',
    text: 'Hello! Please upload a document to get started. I can help you analyze the document, check for grammar issues, and suggest improvements.'
  });
  nextTick(scrollToBottom);
};

// New method to set messages array from parent
const setMessages = (newMessages) => {
  messages.value = newMessages;
  nextTick(scrollToBottom);
};

// Watch documentLoaded prop to show welcome when document is loaded
watch(() => props.documentLoaded, (newVal) => {
  if (newVal && messages.value.length === 0) {
    addWelcomeMessage();
  }
});

onMounted(() => {
  if (messages.value.length === 0) {
    addWelcomeMessage();
  }
});

// Expose methods and reactive state to parent
defineExpose({
  addWelcomeMessage,
  setMessages,
  messages
});
</script>

<style scoped>
/* Your existing styles here, unchanged */
.chat-interface {
  position: relative;
  border-radius: 0;
}
.chat-header {
  background-color: #885053;
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
  background-color: #D5573B;
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}
.assistant-message {
  align-self: flex-start;
  background-color: #C6ECAE;
  color: #333;
  margin-right: auto;
  border-bottom-left-radius: 4px;
}
.message-content {
  line-height: 1.4;
  white-space: pre-line;
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
