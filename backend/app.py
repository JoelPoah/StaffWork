from flask import Flask, request, jsonify

from flask_cors import CORS

from Validation import *
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'


@app.route('/validate', methods=['POST'])
def validate_docx():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    if not filename.endswith('.docx'):
        return jsonify({"error": "Only .docx files are allowed"}), 400

    # Save file
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(filepath)

    # Process the file
    try:
        zip_path = convert_docx_to_zip(Path(filepath))
        extract_dir = extract_zip_to_unique_folder(zip_path)
        xml_path = extract_dir / "word" / "document.xml"
        
        if not xml_path.exists():
            return jsonify({"error": "Invalid DOCX file structure"}), 400
            
        results = validate_docx_structure(xml_path, extract_dir)
        
        # Add validation complete message
        if "summary" in results["errors"]:
            results["errors"]["summary"].append({
                "type": "success",
                "category": "general",
                "message": "Validation complete."
            })
            
        return jsonify(results), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"status": "Backend API is running"}), 200

# === MAIN RUNNER ===
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
