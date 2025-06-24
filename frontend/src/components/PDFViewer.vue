<template>
  <div>
    <!-- <h2>
      Backend processes the docx → highlights errors → converts to pdf → sends to frontend for review.
    </h2>
     -->
    <!-- <button @click="showPdf = true" class="btn">View PDF</button> -->

    <!-- Show PdfApp only after button is clicked -->
    <PdfApp
      v-if="showPdf"
      style="height: 90vh"
      :pdf="pdfPath"
    />
  </div>
</template>

<script>
import PdfApp from "vue3-pdf-app";
import "vue3-pdf-app/dist/icons/main.css";

export default {
  name: "App",
  components: {
    PdfApp,
  },
  data() {
    return {
      showPdf: true,
      pdfPath: "/sample.pdf", // Assuming the PDF is in /public/sample.pdf
    };
  },
};
</script>

<style>
.btn {
  margin: 10px 0;
  padding: 8px 16px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn:hover {
  background-color: #1565c0;
}
</style>
