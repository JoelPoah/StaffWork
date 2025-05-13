from flask import Flask, request, jsonify
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# === HELPER FUNCTIONS ===
def convert_docx_to_zip(docx_path):
    zip_path = docx_path.with_suffix('.zip')
    shutil.copy(docx_path, zip_path)
    return zip_path

def extract_zip_to_unique_folder(zip_path, base_extract_dir=EXTRACT_FOLDER):
    zip_path = Path(zip_path)
    folder_name = zip_path.stem + "_unzipped"
    extract_dir = Path(base_extract_dir) / folder_name
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    return extract_dir

def get_attr(elem, attr):
    return elem.attrib.get(f'{{{W}}}{attr}')

def validate_page_size_margins(root, issues):
    ns = {'w': W}
    pgSz = root.find('.//w:sectPr/w:pgSz', ns)
    if get_attr(pgSz, 'w') != '12240' or get_attr(pgSz, 'h') != '15840' or get_attr(pgSz, 'orient') != 'portrait':
        issues.append("Page size or orientation NOT set to A4 portrait (w=12240, h=15840).")

    pgMar = root.find('.//w:sectPr/w:pgMar', ns)
    expected = {'top': '1418', 'right': '1418', 'bottom': '1418', 'left': '1418', 'header': '567', 'footer': '567', 'gutter': '0'}
    if any(get_attr(pgMar, k) != v for k, v in expected.items()):
        issues.append("Margins NOT set to 2.5cm correctly.")
    return issues

def validate_font_size(root, issues):
    ns = {'w': W}
    for i, rPr in enumerate(root.findall('.//w:rPr', ns), 1):
        sz = rPr.find('w:sz', ns)
        szCs = rPr.find('w:szCs', ns)
        sz_val = get_attr(sz, 'val') if sz is not None else None
        szCs_val = get_attr(szCs, 'val') if szCs is not None else None
        if (sz_val not in ['28', '24'] and sz_val is not None) or (szCs_val not in ['28', '24'] and szCs_val is not None):
            issues.append(f"Line {i}: font size sz={sz_val}, szCs={szCs_val}")
    return issues

def validate_font_type(root, issues):
    ns = {'w': W}
    allowed_fonts = ['Times New Roman', None, "None"]
    for i, rPr in enumerate(root.findall('.//w:rPr', ns), 1):
        rFonts = rPr.find('w:rFonts', ns)
        if rFonts is not None:
            if any(get_attr(rFonts, k) not in allowed_fonts for k in ['ascii', 'hAnsi', 'cs']):
                issues.append(f"Line {i}: font not Times New Roman")
    return issues

def validate_docx_structure(document_xml_path):
    issues = []
    tree = ET.parse(document_xml_path)
    root = tree.getroot()
    issues = validate_page_size_margins(root, issues)
    issues = validate_font_type(root, issues)
    issues = validate_font_size(root, issues)
    return issues

# === FLASK ROUTE ===
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
        results = validate_docx_structure(xml_path)
        results.append("Validation complete.")
        return jsonify({"errors": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === MAIN RUNNER ===
if __name__ == '__main__':
    app.run(debug=True, port=5000)
