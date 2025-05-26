import { createApp } from 'vue'
import App from './App.vue'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

// Custom theme based on the provided color palette
const customTheme = {
  dark: false,
  colors: {
    primary: '#D5573B',    // Jasper
    secondary: '#885053',  // Rose taupe
    accent: '#777DA7',     // Glaucous
    success: '#94C9A9',    // Cambridge blue
    info: '#C6ECAE',       // Tea green
    warning: '#D5573B',    // Jasper
    error: '#D5573B',      // Jasper
    background: '#f5f5f5', // Light background
    surface: '#ffffff',    // White surface
  }
}

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    }
  },
  theme: {
    defaultTheme: 'customTheme',
    themes: {
      customTheme,
    }
  }
})

createApp(App).use(vuetify).mount('#app')
