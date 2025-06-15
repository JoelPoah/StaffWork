from flask import Flask, request, jsonify
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import uuid
import base64
from werkzeug.utils import secure_filename
import html

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'

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

def get_attr(elem, attr, namespace=W):
    return elem.attrib.get(f'{{{namespace}}}{attr}')

def get_text_from_element(element, ns):
    """Extract text from a paragraph or run element"""
    text = ""
    for t in element.findall('.//w:t', ns):
        text += t.text if t.text else ""
    return text

def normalize_text(text):
    # Collapse whitespace and remove hidden characters
    return re.sub(r'\s+', '', text.replace('\u00A0', ' ')).strip()

def is_all_caps(text):
    return text.isupper() and any(c.isalpha() for c in text)

def is_date_like(text):
    text = normalize_text(text).replace(' ', '')

    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',              # 28/05/2025
        r'\d{4}-\d{1,2}-\d{1,2}',                # 2025-05-28
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\d{1,2},?\d{4}',  # May28,2025
        r'\d{1,2}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\d{4}',    # 28May2025
        r'\d{6}h-\d{6}h(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{4}',    # 270800H-280800HMay2025
        r'\d{4}h-\d{4}h(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{4}',    # 2708H-2808HMay2025
    ]

    for pattern in date_patterns:
        if re.search(pattern, text.lower()):
            return True
    return False



def validate_page_justify(root, issues):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    unjustified_paragraphs = []

    for paragraph in root.findall('.//w:p', ns):
        text_parts = []
        for run in paragraph.findall('.//w:r', ns):
            text_elem = run.find('w:t', ns)
            if text_elem is not None and text_elem.text:
                text_parts.append(text_elem.text.strip())

        paragraph_text = ' '.join(text_parts).strip()

        # Skip empty, all-caps, or date-like paragraphs
        if not paragraph_text or is_all_caps(paragraph_text) or is_date_like(paragraph_text):
            continue

        pPr = paragraph.find('w:pPr', ns)
        is_heading = False
        justification = 'left'  # default assumption

        if pPr is not None:
            # Check if paragraph is a heading style
            pStyle = pPr.find('w:pStyle', ns)
            if pStyle is not None:
                style_val = pStyle.attrib.get(f'{{{ns["w"]}}}val', '')
                if style_val.lower().startswith('heading'):
                    is_heading = True

            # Get actual justification if defined
            jc = pPr.find('w:jc', ns)
            if jc is not None:
                justification = jc.attrib.get(f'{{{ns["w"]}}}val', 'left')

        if not is_heading and justification != 'both':
            unjustified_paragraphs.append({
                'text': paragraph_text,
                'justification': justification
            })
    if unjustified_paragraphs:
         issues.append({
            "type": "error",
            "category": "formatting",
            "message": "Paragraph not justified."
        })

    return issues





def validate_page_size_margins(root, issues):
    """Validate page size and margins"""
    ns = {'w': W}
    pgSz = root.find('.//w:sectPr/w:pgSz', ns)

    if pgSz is None:
        issues.append({
            "type": "error",
            "category": "formatting",
            "message": "Page size settings not found."
        })
        return issues
        
    if get_attr(pgSz, 'w') != '12240' or get_attr(pgSz, 'h') != '15840' or get_attr(pgSz, 'orient') != 'portrait':
        issues.append({
            "type": "error",
            "category": "formatting",
            "message": "Page size or orientation NOT set to A4 portrait (w=12240, h=15840)."
        })

    pgMar = root.find('.//w:sectPr/w:pgMar', ns)
    expected = {'top': '1418', 'right': '1418', 'bottom': '1418', 'left': '1418', 'header': '567', 'footer': '567', 'gutter': '0'}
    
    if pgMar is None:
        issues.append({
            "type": "error",
            "category": "formatting",
            "message": "Page margin settings not found."
        })
        return issues
        
    if any(get_attr(pgMar, k) != v for k, v in expected.items()):
        issues.append({
            "type": "error",
            "category": "formatting",
            "message": "Margins NOT set to 2.5cm correctly."
        })
    return issues

def extract_word_level_errors(root, extract_dir):
    """Extract word-level errors for font size and type"""
    ns = {'w': W}
    word_errors = {}
    
    # Get relationship data for image references
    rels_path = extract_dir / "word" / "_rels" / "document.xml.rels"
    image_rels = {}
    if rels_path.exists():
        try:
            rels_tree = ET.parse(rels_path)
            rels_root = rels_tree.getroot()
            for rel in rels_root.findall('./Relationship', {'': R}):
                rel_id = rel.attrib.get('Id')
                rel_type = rel.attrib.get('Type')
                rel_target = rel.attrib.get('Target')
                if rel_type and 'image' in rel_type:
                    image_rels[rel_id] = rel_target
        except Exception as e:
            print(f"Error parsing relationships: {e}")
    
    # Process paragraphs
    for para_idx, para in enumerate(root.findall('.//w:p', ns), 1):
        para_text = get_text_from_element(para, ns)
        
        # Process runs within paragraph
        current_position = 0
        for run_idx, run in enumerate(para.findall('.//w:r', ns), 1):
            run_text = get_text_from_element(run, ns)
            if not run_text:
                continue
                
            # Check for properties
            rPr = run.find('w:rPr', ns)
            if rPr is not None:
                # Check font size
                sz = rPr.find('w:sz', ns)
                szCs = rPr.find('w:szCs', ns)
                sz_val = get_attr(sz, 'val') if sz is not None else None
                szCs_val = get_attr(szCs, 'val') if szCs is not None else None
                
                # Check font type
                rFonts = rPr.find('w:rFonts', ns)
                font_errors = []
                
                if rFonts is not None:
                    allowed_fonts = ['Times New Roman', None, "None"]
                    if any(get_attr(rFonts, k) not in allowed_fonts for k in ['ascii', 'hAnsi', 'cs']):
                        font_name = get_attr(rFonts, 'ascii') or get_attr(rFonts, 'hAnsi') or "Unknown"
                        font_errors.append({
                            "type": "error",
                            "message": f"Font should be Times New Roman, found {font_name}"
                        })
                
                # Check font size
                size_errors = []
                if (sz_val not in ['28', '24'] and sz_val is not None) or (szCs_val not in ['28', '24'] and szCs_val is not None):
                    size_errors.append({
                        "type": "warning",
                        "message": f"Font size should be 14pt (28) or 12pt (24), found {sz_val or szCs_val}"
                    })
                
                # If we have errors, add to word_errors
                if font_errors or size_errors:
                    for word in run_text.split():
                        if word.strip():
                            word_id = f"word_{uuid.uuid4().hex[:8]}"
                            word_errors[word_id] = {
                                "word": word,
                                "paragraph": para_idx,
                                "position": current_position,
                                "errors": font_errors + size_errors
                            }
                        current_position += len(word) + 1
                else:
                    current_position += len(run_text)
            
            # Check for images and references
            drawing = run.find('.//w:drawing', ns)
            if drawing is not None:
                try:
                    # Extract image info
                    blip = drawing.find('.//a:blip', {'a': A})
                    if blip is not None:
                        embed_id = get_attr(blip, 'embed', namespace=R)
                        if embed_id in image_rels:
                            image_path = image_rels[embed_id]
                            # Add image reference info
                            img_id = f"img_{uuid.uuid4().hex[:8]}"
                            word_errors[img_id] = {
                                "word": "[IMAGE]",
                                "paragraph": para_idx,
                                "position": current_position,
                                "is_image": True,
                                "image_path": image_path,
                                "errors": [{
                                    "type": "info",
                                    "message": f"Image found: {image_path}"
                                }]
                            }
                except Exception as e:
                    print(f"Error processing image: {e}")
    
    return word_errors

def extract_image_references(root, word_errors):
    """Extract and validate image references"""
    ns = {'w': W}
    image_references = []
    
    # Regular expression to find figure references
    ref_pattern = re.compile(r'fig(?:ure)?\.?\s*(\d+)', re.IGNORECASE)
    
    # Find all paragraphs with potential references
    for para_idx, para in enumerate(root.findall('.//w:p', ns), 1):
        para_text = get_text_from_element(para, ns)
        
        # Find references in text
        matches = ref_pattern.finditer(para_text)
        for match in matches:
            ref_num = match.group(1)
            ref_id = f"ref_{uuid.uuid4().hex[:8]}"
            
            # Check if this reference is valid (image exists)
            valid = any(
                error_info.get("is_image", False) and 
                f"image{ref_num}" in error_info.get("image_path", "").lower()
                for error_info in word_errors.values()
            )
            
            image_references.append({
                "id": ref_id,
                "reference": match.group(0),
                "number": ref_num,
                "paragraph": para_idx,
                "position": match.start(),
                "valid": valid
            })
    
    return image_references

def extract_document_content(root, word_errors, image_references):
    """Extract document content with word-level error markup"""
    ns = {'w': W}
    content = []
    
    # Process paragraphs
    for para_idx, para in enumerate(root.findall('.//w:p', ns), 1):
        para_text = get_text_from_element(para, ns)
        if not para_text.strip():
            content.append("<p>&nbsp;</p>")
            continue
        
        # Start paragraph
        para_content = "<p>"
        
        # Process runs within paragraph
        current_position = 0
        for run in para.findall('.//w:r', ns):
            run_text = get_text_from_element(run, ns)
            if not run_text:
                continue
            
            # Process each word in the run
            words = run_text.split()
            for i, word in enumerate(words):
                # Check if this word has errors
                error_word_id = None
                for word_id, error_info in word_errors.items():
                    if (error_info.get("paragraph") == para_idx and 
                        error_info.get("word") == word and 
                        abs(error_info.get("position", 0) - current_position) < 10):
                        error_word_id = word_id
                        break
                
                # Check if this word is part of an image reference
                ref_id = None
                for ref in image_references:
                    if (ref.get("paragraph") == para_idx and 
                        current_position >= ref.get("position", 0) and 
                        current_position < ref.get("position", 0) + len(ref.get("reference", ""))):
                        ref_id = ref.get("id")
                        break
                
                # Add word with appropriate markup
                if error_word_id:
                    error_info = word_errors[error_word_id]
                    error_types = [err.get("type") for err in error_info.get("errors", [])]
                    
                    if "error" in error_types:
                        class_name = "error-word"
                    elif "warning" in error_types:
                        class_name = "warning-word"
                    else:
                        class_name = "doc-word"
                    
                    para_content += f'<span id="{error_word_id}" class="doc-word {class_name}">{html.escape(word)}</span>'
                elif ref_id:
                    ref_info = next((r for r in image_references if r.get("id") == ref_id), None)
                    if ref_info:
                        class_name = "valid-ref" if ref_info.get("valid") else "invalid-ref"
                        para_content += f'<span data-ref-id="{ref_id}" class="img-ref {class_name}">{html.escape(word)}</span>'
                    else:
                        para_content += html.escape(word)
                else:
                    para_content += html.escape(word)
                
                # Add space between words
                if i < len(words) - 1:
                    para_content += " "
                    current_position += len(word) + 1
                else:
                    current_position += len(word)
        
        # End paragraph
        para_content += "</p>"
        content.append(para_content)
    
    return "\n".join(content)

def extract_images(extract_dir):
    """Extract images from the document"""
    images_dir = extract_dir / "word" / "media"
    images = []
    
    if images_dir.exists():
        for img_file in images_dir.glob("*"):
            if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                try:
                    with open(img_file, 'rb') as f:
                        img_data = f.read()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                    images.append({
                        "name": img_file.name,
                        "path": str(img_file.relative_to(extract_dir)),
                        "data": f"data:image/{img_file.suffix[1:]};base64,{img_base64}"
                    })
                except Exception as e:
                    print(f"Error processing image {img_file}: {e}")
    
    return images

def validate_docx_structure(document_xml_path, extract_dir):
    """Validate DOCX structure and extract content with error mapping"""
    tree = ET.parse(document_xml_path)
    root = tree.getroot()
    print(root)
    # Initialize result containers
    issues = []
    
    # Validate page size and margins
    issues = validate_page_size_margins(root, issues)
    issues = validate_page_justify(root, issues)
   

    # Extract word-level errors
    word_errors = extract_word_level_errors(root, extract_dir)
    
    # Extract image references
    image_references = extract_image_references(root, word_errors)
    
    # Extract images
    images = extract_images(extract_dir)
    
    # Extract document content with error markup
    content = extract_document_content(root, word_errors, image_references)
    
    # Add summary information
    font_error_count = sum(1 for info in word_errors.values() 
                          if any(err.get("type") == "error" and "Font" in err.get("message", "") 
                                for err in info.get("errors", [])))
    
    size_error_count = sum(1 for info in word_errors.values() 
                          if any(err.get("type") == "warning" and "Font size" in err.get("message", "") 
                                for err in info.get("errors", [])))
    
    invalid_ref_count = sum(1 for ref in image_references if not ref.get("valid"))
    
    # Add summary issues
    if font_error_count > 0:
        issues.append({
            "type": "error",
            "category": "fonts",
            "message": f"Found {font_error_count} words with incorrect font type."
        })
    
    if size_error_count > 0:
        issues.append({
            "type": "warning",
            "category": "fonts",
            "message": f"Found {size_error_count} words with incorrect font size."
        })
    
    if invalid_ref_count > 0:
        issues.append({
            "type": "warning",
            "category": "images",
            "message": f"Found {invalid_ref_count} invalid image references."
        })
    
    if len(images) > 0:
        issues.append({
            "type": "info",
            "category": "images",
            "message": f"Found {len(images)} images in the document."
        })
    
    # Categorize issues
    categorized_errors = {
        "summary": issues,
        "formatting": [issue for issue in issues if issue.get("category") == "formatting"],
        "fonts": [issue for issue in issues if issue.get("category") == "fonts"],
        "images": [issue for issue in issues if issue.get("category") == "images"]
    }
    
    return {
        "errors": categorized_errors,
        "word_errors": word_errors,
        "image_references": image_references,
        "images": images,
        "content": content
    }
