import docx
import os
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def extract_font_information(file_path):
    """Extract detailed font information from a Word document, including style definitions."""
    print(f"Analyzing document: {file_path}")
    doc = docx.Document(file_path)
    
    # Dictionary to store font information
    font_info = {}
    style_info = {}
    
    # Extract style information
    print("\nSTYLE DEFINITIONS:")
    for style in doc.styles:
        if hasattr(style, 'font') and style.font:
            font_name = style.font.name
            font_size = style.font.size
            
            # Convert font size from docx internal units to points if it exists
            if font_size is not None:
                # Font size in docx is in half-points
                font_size_pt = font_size / 12.0
            else:
                font_size_pt = "Default"
                
            style_info[style.name] = {
                'font_name': font_name,
                'font_size_pt': font_size_pt
            }
            
            print(f"Style: {style.name}, Font: {font_name}, Size: {font_size_pt}")
    
    # Extract document default font information
    print("\nDOCUMENT DEFAULT SETTINGS:")
    try:
        default_font = doc.styles['Normal'].font
        default_font_name = default_font.name
        default_font_size = default_font.size
        
        if default_font_size is not None:
            default_font_size_pt = default_font_size / 12.0
        else:
            default_font_size_pt = "Default"
            
        print(f"Default Font: {default_font_name}, Size: {default_font_size_pt}")
    except:
        print("Could not determine document default settings")
    
    # Extract XML-level font information
    print("\nXML-LEVEL FONT INFORMATION:")
    try:
        # Get the document's XML
        xml_body = doc._body._element.xml
        
        # Check if Times New Roman is mentioned in the XML
        if "Times New Roman" in xml_body:
            print("Times New Roman font found in document XML")
        else:
            print("Times New Roman font NOT found in document XML")
            
        # Check for font size 14 (28 half-points)
        if "sz w:val=\"28\"" in xml_body:
            print("Font size 14 (28 half-points) found in document XML")
        else:
            print("Font size 14 (28 half-points) NOT found in document XML")
    except:
        print("Could not analyze document XML")
    
    # Analyze paragraphs with more detailed information
    print("\nDETAILED PARAGRAPH ANALYSIS:")
    for i, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip():  # Only analyze non-empty paragraphs
            print(f"\nParagraph {i+1}: '{paragraph.text[:50]}...' if len(paragraph.text) > 50 else paragraph.text")
            print(f"  Style: {paragraph.style.name}")
            
            # Get font information from runs within the paragraph
            for j, run in enumerate(paragraph.runs):
                if run.text.strip():  # Only report on runs with actual text
                    # Try to get direct font information
                    font_name = run.font.name
                    font_size = run.font.size
                    
                    # If direct font info is None, try to get from style
                    if font_name is None and paragraph.style.name in style_info:
                        font_name = style_info[paragraph.style.name]['font_name']
                    
                    if font_size is None and paragraph.style.name in style_info:
                        font_size_pt = style_info[paragraph.style.name]['font_size_pt']
                    else:
                        # Convert font size from docx internal units to points if it exists
                        if font_size is not None:
                            font_size_pt = font_size / 12.0
                        else:
                            font_size_pt = "Default"
                    
                    print(f"  Run {j+1}: Font: {font_name or 'Default'}, Size: {font_size_pt}, Text: '{run.text[:20]}...' if len(run.text) > 20 else run.text")
                    
                    # Try to get XML-level font information for this run
                    try:
                        run_element = run._element.xml
                        if "w:rFonts" in run_element:
                            print(f"    XML font info found in run")
                        if "w:sz" in run_element:
                            print(f"    XML font size info found in run")
                    except:
                        pass
                    
                    # Add to font info dictionary
                    key = f"{font_name}_{font_size_pt}"
                    if key in font_info:
                        font_info[key]['count'] += 1
                        font_info[key]['characters'] += len(run.text)
                    else:
                        font_info[key] = {
                            'font_name': font_name,
                            'font_size_pt': font_size_pt,
                            'count': 1,
                            'characters': len(run.text)
                        }
    
    # Summary of font usage
    print("\nFONT USAGE SUMMARY:")
    for key, info in font_info.items():
        print(f"Font: {info['font_name'] or 'Default'}, Size: {info['font_size_pt']}, Occurrences: {info['count']}, Characters: {info['characters']}")
    
    # Check document properties for theme information
    print("\nDOCUMENT PROPERTIES:")
    try:
        core_properties = doc.core_properties
        print(f"Title: {core_properties.title}")
        print(f"Author: {core_properties.author}")
        print(f"Created: {core_properties.created}")
        print(f"Modified: {core_properties.modified}")
    except:
        print("Could not access document properties")
    
    # Final assessment
    print("\nFINAL ASSESSMENT:")
    # Check if Normal style is Times New Roman 14
    normal_style_correct = False
    if 'Normal' in style_info:
        normal_font = style_info['Normal']['font_name']
        normal_size = style_info['Normal']['font_size_pt']
        
        if normal_font == 'Times New Roman' and normal_size == 14.0:
            normal_style_correct = True
            print("✓ Normal style is set to Times New Roman, size 14")
        else:
            print(f"✗ Normal style is set to {normal_font or 'Default'}, size {normal_size}")
    
    # Check XML for Times New Roman and size 14
    xml_correct = False
    if "Times New Roman" in xml_body and "sz w:val=\"28\"" in xml_body:
        xml_correct = True
        print("✓ Document XML contains Times New Roman font and size 14 references")
    
    # Final verdict
    if normal_style_correct or xml_correct:
        print("\n✓ Document likely meets the requirement: Times New Roman, size 14")
        print("Note: Some text may still have different formatting if explicitly overridden")
    else:
        print("\n✗ Document likely does not meet the requirement: Times New Roman, size 14")
        print("Recommendation: Apply Times New Roman, size 14 to the Normal style and all text in the document")

if __name__ == "__main__":
    file_path = "/home/ubuntu/upload/BEATRICE CHONG_STAFF_PAPER.docx"
    if os.path.exists(file_path):
        extract_font_information(file_path)
    else:
        print(f"File not found: {file_path}")
