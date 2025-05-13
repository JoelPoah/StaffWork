import os
import shutil
import zipfile
from pathlib import Path

# Define WordprocessingML namespace
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def convert_docx_to_zip(docx_path):
    """
    Renames a .docx file to .zip and returns the zip path.
    """
    docx_path = Path(docx_path)
    if docx_path.suffix != '.docx':
        raise ValueError("Input file must be a .docx file")

    zip_path = docx_path.with_suffix('.zip')
    shutil.copy(docx_path, zip_path)
    print(f"Converted {docx_path.name} to {zip_path.name}")
    return zip_path

def extract_zip_to_unique_folder(zip_path, base_extract_dir="extracted"):
    """
    Extracts the zip file to a unique folder based on filename.
    """
    zip_path = Path(zip_path)
    folder_name = zip_path.stem + "_unzipped"
    extract_dir = Path(base_extract_dir) / folder_name
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Extracted to: {extract_dir}")
    return extract_dir



import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile


# Function to convert twips to centimeters
def twips_to_cm(twips):
    inches = twips / 1440
    return inches * 2.54



# Helper to access namespaced attributes
def get_attr(elem, attr):
    return elem.attrib.get(f'{{{W}}}{attr}')







# All functions below are for validating the structure of the document.xml file


def validate_page_size_margins(root,issues):
    ns = {'w': W}
    # Check page size
    pgSz = root.find('.//w:sectPr/w:pgSz', ns)
    if get_attr(pgSz, 'w') != '12240' or \
       get_attr(pgSz, 'h') != '15840' or \
       get_attr(pgSz, 'orient') != 'portrait':
        issues.append("Page size or orientation NOT set to A4 portrait (w=12240, h=15840). Could be due to margins.")

    # Check margins
    pgMar = root.find('.//w:sectPr/w:pgMar', ns)
    expected_margins = {
        'top': '1418',
        'right': '1418',
        'bottom': '1418',
        'left': '1418',
        'header': '567',
        'footer': '567',
        'gutter': '0'
    }
    if any(get_attr(pgMar, k) != v for k, v in expected_margins.items()):
        # show the current values of the margins
        issues.append("Margin of 2.5cm NOT reflected")
    return issues

def validate_font_size(root,issues):
    ns = {'w':W}
    # Loop through all rPr (run properties) blocks
    for i, rPr in enumerate(root.findall('.//w:rPr', ns), start=1):
        rFonts = rPr.find('w:rFonts', ns)

        # Ensure rFonts exists and check font declarations
        if rFonts is not None:
            ascii_font = get_attr(rFonts, 'ascii')
            hAnsi_font = get_attr(rFonts, 'hAnsi')
            cs_font = get_attr(rFonts, 'cs')

            # Check if the fonts are not "Times New Roman"
            if ascii_font != 'Times New Roman' or hAnsi_font != 'Times New Roman' or cs_font != 'Times New Roman':
                issues.append(f"Line {i}: ascii={ascii_font}, hAnsi={hAnsi_font}, cs={cs_font}")

        # Check font size (w:sz and w:szCs)
        sz = rPr.find('w:sz', ns)
        szCs = rPr.find('w:szCs', ns)
        sz_val = get_attr(sz, 'val') if sz is not None else None
        szCs_val = get_attr(szCs, 'val') if szCs is not None else None

        # Check if either sz or szCs is neither 28 nor 24 (ignore None)
        if (sz_val not in ['28', '24'] and sz_val is not None) or \
           (szCs_val not in ['28', '24'] and szCs_val is not None):
            issues.append(f"Line {i}: font size w:sz={sz_val}, w:szCs={szCs_val} (expected 28 for 14pt or 24 for 12pt)")

    return issues

def validate_font_type(root,issues):
    ns = {'w': W}
    
    allowed_fonts = ['Times New Roman', None,"None"]
    # Loop through all rPr (run properties) blocks
    for i, rPr in enumerate(root.findall('.//w:rPr', ns), start=1):
        rFonts = rPr.find('w:rFonts', ns)

        # Ensure rFonts exists and check font declarations
        if rFonts is not None:
            ascii_font = get_attr(rFonts, 'ascii')
            hAnsi_font = get_attr(rFonts, 'hAnsi')
            cs_font = get_attr(rFonts, 'cs')

            # Check if the fonts are not in the allowed list
            if ascii_font not in allowed_fonts or hAnsi_font not in allowed_fonts or cs_font not in allowed_fonts:
                issues.append(f"Line {i}: ascii={ascii_font}, hAnsi={hAnsi_font}, cs={cs_font}")
    return issues

def validate_line_spacing(root,issues):
    '''
    Validates line spacing in the document.xml file looking at the w:line feature.
    However this may not be working properly 
    
    '''
    ns = {'w': W}
    # Loop through all rPr (run properties) blocks
    for i, rPr in enumerate(root.findall('.//w:rPr', ns), start=1):
        spacing = rPr.find('w:spacing', ns)
        if spacing is not None:
            line = get_attr(spacing, 'line')
            lineRule = get_attr(spacing, 'lineRule')
            if line != '240' or lineRule != 'auto':
                issues.append(f"Line {i}: line={line}, lineRule={lineRule} (expected 240 and auto)")
    return issues

def validate_underline_bold(root,issues):
    '''Checks whether any fullstop is underlined or bolded. If it is raise an issue
    Looks good but not tested
    '''
    ns = {'w': W}
    # Find all text that are underlined 
    underlined_texts = root.findall('.//w:u', ns)
    # Find all text that are bolded
    bolded_texts = root.findall('.//w:b', ns)
    # Check if any of the texts are underlined or bolded
    if underlined_texts or bolded_texts:
        # Append line in which the underlined or bolded text is found
        for i, text in enumerate(underlined_texts + bolded_texts, start=1):
            if text.text and '.' in text.text:
                issues.append(f"Line {i}: Found underlined or bolded text with fullstop: {text.text}")
    return issues

def validate_justified_text(root,issues):
    '''Checks whether any text is justified. If it is raise an issue
    Looks good but not tested
    '''
    jc_values={'left':'Left-aligned',
    'center':'Centered',
    'right':'Right-aligned',
    'both':'Justified'}
    
    ns = {'w': W}
    # Find all text that are justified 
    justified_texts = root.findall('.//w:jc', ns)
    # Check if any of the texts are justified
    if justified_texts:
        # Append line in which the justified text is found
        for i, text in enumerate(justified_texts, start=1):
            if text.text and 'center' in text.text:
                issues.append(f"Line {i}: Found justified text: {text.text}")
    return issues




def validate_docx_structure(document_xml_path):
    """
    Validates the structure of the document.xml file in a .docx file.
    """
    issues = []

    # Parse XML
    tree = ET.parse(document_xml_path)
    root = tree.getroot()


    # Validate page size and margins
    issues = validate_page_size_margins(root,issues)
    
    # Validate font properties
    issues = validate_font_type(root,issues)
    issues = validate_font_size(root,issues)
    # Validate line spacing
    issues = validate_line_spacing(root,issues)
    
    # Validate underline and bold
    issues = validate_underline_bold(root,issues)
    # Validate justified text
    issues = validate_justified_text(root,issues)
    
    return issues





# Example usage:
# docx_path = "Papers/BRYAN_KOH_ZI_QIN_XRG_MSW.docx"
docx_path = "Papers/BEATRICE.docx"
zip_path = convert_docx_to_zip(docx_path)
extract_dir = extract_zip_to_unique_folder(zip_path)
xml_path = extract_dir / "word" / "document.xml"
xml_path = "extracted/BRYAN_KOH_ZI_QIN_XRG_MSW_unzipped/word/document.xml"
xml_path = "extracted/BEATRICE_unzipped/word/document.xml"
results = validate_docx_structure(xml_path)

results.append("Validation complete. You should always check the sensitivity of your document.")

print("Validation Results:")
# Print the results
for issue in results:
    if isinstance(issue, list):
        for sub_issue in issue:
            print(sub_issue)
    else:
        print(issue)
