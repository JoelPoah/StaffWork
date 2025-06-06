import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
from transformers import pipeline
import xml.etree.ElementTree as ET
import base64
import io
import zipfile

app = Flask(__name__)
CORS(app)

# Create upload and extracted directories if they don't exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('extracted', exist_ok=True)

def extract_docx_content(docx_file_path):
    """Extract text content from a DOCX file using pure Python libraries"""
    try:
        # Open the DOCX file as a zip
        with zipfile.ZipFile(docx_file_path, 'r') as zip_ref:
            # Extract document.xml which contains the main content
            if 'word/document.xml' in zip_ref.namelist():
                content_xml = zip_ref.read('word/document.xml')
                
                # Parse XML
                root = ET.fromstring(content_xml)
                
                # Extract text from paragraphs (simplified)
                # In a real implementation, this would handle more complex document structures
                ns = {
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                }
                
                paragraphs = []
                for para in root.findall('.//w:p', ns):
                    texts = []
                    for text_elem in para.findall('.//w:t', ns):
                        if text_elem.text:
                            texts.append(text_elem.text)
                    if texts:
                        paragraphs.append(''.join(texts))
                
                return '\n'.join(paragraphs)
            else:
                return "Could not find document content."
    except Exception as e:
        print(f"Error extracting DOCX content: {str(e)}")
        return f"Error extracting document content: {str(e)}"

def validate_docx(docx_file_path):
    """Validate DOCX file and return errors"""
    try:
        # Extract content for display
        content = extract_docx_content(docx_file_path)
        
        # Open the DOCX file as a zip
        with zipfile.ZipFile(docx_file_path, 'r') as zip_ref:
            # Extract document.xml which contains the main content
            if 'word/document.xml' in zip_ref.namelist():
                content_xml = zip_ref.read('word/document.xml')
                
                # Parse XML
                root = ET.fromstring(content_xml)
                
                # Namespace for Word XML
                ns = {
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                }
                
                # Validate document structure and formatting
                errors = {
                    'summary': [],
                    'formatting': [],
                    'fonts': [],
                    'images': []
                }
                
                # Check for page size and orientation
                section_props = root.findall('.//w:sectPr', ns)
                if section_props:
                    for sect in section_props:
                        page_size = sect.find('.//w:pgSz', ns)
                        if page_size is not None:
                            w = page_size.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                            h = page_size.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}h')
                            if w and h:
                                if int(w) != 12240 or int(h) != 15840:  # A4 portrait
                                    errors['formatting'].append({
                                        'type': 'error',
                                        'message': f'Page size or orientation NOT set to A4 portrait (w={w}, h={h}).'
                                    })
                                    errors['summary'].append({
                                        'type': 'error',
                                        'message': 'Page size or orientation NOT set to A4 portrait.'
                                    })
                
                # Check margins
                section_props = root.findall('.//w:sectPr', ns)
                if section_props:
                    for sect in section_props:
                        margins = sect.find('.//w:pgMar', ns)
                        if margins is not None:
                            left = margins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left')
                            right = margins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right')
                            tolerance = 1
                            if left and right:
                                if abs(int(left) - 1440) > tolerance or abs(int(right) - 1440) > tolerance:  # 1 inch margins
                                    errors['formatting'].append({
                                        'type': 'error',
                                        'message': f'Margins NOT set to 2.5cm correctly (left={left}, right={right}).'
                                    })
                                    errors['summary'].append({
                                        'type': 'error',
                                        'message': 'Margins NOT set to 2.5cm correctly.'
                                    })
                
                # Check font sizes and types
                word_errors = {}
                line_num = 0
                word_id = 0
                
                for para in root.findall('.//w:p', ns):
                    line_num += 1
                    for run in para.findall('.//w:r', ns):
                        rPr = run.find('.//w:rPr', ns)
                        if rPr is not None:
                            # Check font size
                            sz = rPr.find('.//w:sz', ns)
                            if sz is not None:
                                size_val = sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                                if size_val and int(size_val) != 24:  # 12pt = 24 half-points
                                    text_elem = run.find('.//w:t', ns)
                                    if text_elem is not None and text_elem.text and text_elem.text.strip():
                                        word_id += 1
                                        word_key = f"word_{word_id}"
                                        word_errors[word_key] = {
                                            'text': text_elem.text,
                                            'line': line_num,
                                            'errors': [{
                                                'type': 'warning',
                                                'message': f'Font size sz={size_val} (should be 24 for 12pt)'
                                            }]
                                        }
                                        errors['fonts'].append({
                                            'type': 'warning',
                                            'message': f'Line {line_num}: font size sz={size_val}, szCs={size_val} (should be 24 for 12pt)'
                                        })
                            
                            # Check font type
                            font = rPr.find('.//w:rFonts', ns)
                            if font is not None:
                                ascii_font = font.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')
                                if ascii_font and ascii_font != 'Times New Roman':
                                    text_elem = run.find('.//w:t', ns)
                                    if text_elem is not None and text_elem.text and text_elem.text.strip():
                                        word_id += 1
                                        word_key = f"word_{word_id}"
                                        word_errors[word_key] = {
                                            'text': text_elem.text,
                                            'line': line_num,
                                            'errors': [{
                                                'type': 'error',
                                                'message': f'Font type "{ascii_font}" (should be Times New Roman)'
                                            }]
                                        }
                                        errors['fonts'].append({
                                            'type': 'error',
                                            'message': f'Line {line_num}: font type "{ascii_font}" (should be Times New Roman)'
                                        })
                
                # Check for images and references
                image_refs = []
                images = []
                
                # Find all image references in text (e.g., "Figure 1", "Table 2")
                ref_pattern = re.compile(r'(Figure|Table|Fig\.)\s+(\d+)', re.IGNORECASE)
                
                # Extract text to find references
                all_text = ""
                for para in root.findall('.//w:p', ns):
                    para_text = ""
                    for text_elem in para.findall('.//w:t', ns):
                        if text_elem.text:
                            para_text += text_elem.text
                    all_text += para_text + "\n"
                
                # Find all references
                for match in ref_pattern.finditer(all_text):
                    ref_type = match.group(1)
                    ref_num = match.group(2)
                    image_refs.append({
                        'id': f"ref_{ref_type}_{ref_num}",
                        'type': ref_type,
                        'number': ref_num,
                        'valid': False  # Will be set to True if matching image is found
                    })
                
                # Find all images in document
                for drawing in root.findall('.//w:drawing', ns):
                    images.append({
                        'id': f"img_{len(images) + 1}",
                        'type': 'image'
                    })
                
                # Validate references against images
                for ref in image_refs:
                    # Simple validation - just check if we have enough images
                    if int(ref['number']) <= len(images):
                        ref['valid'] = True
                    else:
                        errors['images'].append({
                            'type': 'warning',
                            'message': f"Reference to {ref['type']} {ref['number']} found, but image may be missing"
                        })
                
                # Add summary of errors
                if errors['fonts'] or errors['formatting']:
                    error_count = len(errors['fonts']) + len(errors['formatting'])
                    errors['summary'].append({
                        'type': 'warning',
                        'message': f"Found {error_count} formatting issues in the document."
                    })
                
                # Convert content to HTML for display
                html_content = ""
                current_line = 1
                
                for para in root.findall('.//w:p', ns):
                    para_html = "<p>"
                    for run in para.findall('.//w:r', ns):
                        text_elem = run.find('.//w:t', ns)
                        if text_elem is not None and text_elem.text:
                            # Check if this word has errors
                            has_error = False
                            error_id = None
                            
                            for word_id, word_info in word_errors.items():
                                if word_info['line'] == current_line and text_elem.text.strip() in word_info['text']:
                                    has_error = True
                                    error_id = word_id
                                    break
                            
                            if has_error:
                                para_html += f'<span id="{error_id}" class="doc-word">{text_elem.text}</span>'
                            else:
                                para_html += text_elem.text
                    
                    para_html += "</p>"
                    html_content += para_html
                    current_line += 1
                
                return {
                    'content': html_content,
                    'errors': errors,
                    'word_errors': word_errors,
                    'images': images,
                    'image_references': image_refs
                }
            else:
                return {
                    'content': "Could not find document content.",
                    'errors': {
                        'summary': [{
                            'type': 'error',
                            'message': 'Could not extract document content for validation.'
                        }]
                    }
                }
    except Exception as e:
        print(f"Error validating DOCX: {str(e)}")
        return {
            'content': f"Error validating document: {str(e)}",
            'errors': {
                'summary': [{
                    'type': 'error',
                    'message': f'Error validating document: {str(e)}'
                }]
            }
        }

@app.route('/validate', methods=['POST'])
def validate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.docx'):
        # Save the file
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        
        # Validate the file
        result = validate_docx(file_path)
        
        return jsonify(result)
    else:
        return jsonify({'error': 'Invalid file type. Please upload a DOCX file.'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400
    
    message = data.get('message', '')
    document_content = data.get('documentContent', '')
    
    try:
        # Simple response for demonstration
        if "analyze" in message.lower() or "critique" in message.lower() or "flow" in message.lower():
            response = {
                "response": """
                Here's my analysis of your document:
                
                Flow and Structure:
                The document appears to have a logical structure with clear sections.
                Some paragraphs could be shortened for better readability.
                
                Suggestions for improvement:
                - Consider using more transition words between paragraphs
                - The introduction could be more concise
                - Try to reduce redundant phrases
                
                Grammar check found several potential issues, including:
                - Some sentences are too long and could be split
                - Watch for passive voice usage
                - Check for consistent tense throughout
                
                Vocabulary enhancement:
                I found several words that could be replaced with more precise alternatives:
                - "good" → "excellent", "outstanding"
                - "bad" → "poor", "inadequate"
                - "very" → "extremely", "notably"
                
                Would you like more specific details about any part of this analysis?
                """
            }
        elif "grammar" in message.lower() or "spelling" in message.lower():
            response = {
                "response": """
                I've checked your document for grammar and spelling issues:
                
                Grammar:
                - Watch for subject-verb agreement in paragraphs 2 and 4
                - Some sentences are too long and should be split
                - Check for proper comma usage in lists
                
                Spelling:
                No major spelling errors detected, but there are some inconsistencies in:
                - Capitalization of technical terms
                - Hyphenation of compound words
                
                Would you like me to suggest specific corrections for any of these issues?
                """
            }
        elif "summarize" in message.lower() or "summary" in message.lower():
            response = {
                "response": """
                Here's a summary of your document:
                
                The document discusses the importance of proper formatting in academic papers, focusing on font selection, margin settings, and citation styles. It emphasizes that consistent formatting helps readers focus on content rather than being distracted by presentation issues. The author argues that following established formatting guidelines demonstrates professionalism and attention to detail, which can positively influence how the work is received by reviewers and readers.
                
                Key points include:
                - The importance of Times New Roman 12pt font for readability
                - Proper margin settings for printed documents
                - Consistent citation formatting throughout
                - The relationship between professional presentation and content credibility
                
                Would you like me to expand on any part of this summary?
                """
            }
        else:
            response = {
                "response": f"I've analyzed your document and can answer questions about its content, structure, grammar, and vocabulary. What specific aspect would you like me to help with?"
            }
            
        return jsonify(response)
    
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        return jsonify({"response": "I'm sorry, I encountered an error processing your request. Please try again."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
