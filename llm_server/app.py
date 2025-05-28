import os
import sys
import html
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

app = Flask(__name__)
CORS(app)

# Initialize global variables
model = None
tokenizer = None
llm = None
qa_chain = None
document_content_cache = None

def initialize_model():
    global model, tokenizer, llm
    
    print("Initializing LLM model...")
    
    try:
        # Load model and tokenizer - using a seq2seq model that's better for text generation
        model_name = "google/flan-t5-base"  # Using a smaller model for deployment
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Create pipeline
        pipe = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=512,
            temperature=0.7,
            top_p=0.9,
        )
        
        # Create LangChain LLM
        llm = HuggingFacePipeline(pipeline=pipe)
        
        print("Model initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        return False

def clean_html_content(html_content):
    """Clean HTML content to extract plain text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def create_qa_chain(document_content):
    global llm, qa_chain, document_content_cache
    
    print("Creating QA chain for document...")
    
    try:
        # Clean HTML content if needed
        if '<' in document_content and '>' in document_content:
            document_content = clean_html_content(document_content)
        
        # Cache the document content
        document_content_cache = document_content
        
        # Split document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        texts = text_splitter.split_text(document_content)
        
        if not texts:
            print("Warning: No text chunks created from document")
            return False
        
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create vector store
        docsearch = FAISS.from_texts(texts, embeddings)
        
        # Create QA chain
        prompt_template = """
        You are a document analysis assistant that helps users understand and improve their documents.
        
        Document content:
        {context}
        
        Question: {question}
        
        Provide a helpful, detailed response. If asked to analyze the document, critique the flow of the writer's thoughts,
        suggest how it can be shortened and made more concise, detect grammar mistakes, and suggest better vocabulary.
        
        Answer:
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template, 
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=docsearch.as_retriever(),
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        print("QA chain created successfully")
        return True
    except Exception as e:
        print(f"Error creating QA chain: {str(e)}")
        return False

def analyze_document_flow(document_content):
    """Analyze document flow and structure"""
    global llm
    
    try:
        # Clean HTML content if needed
        if '<' in document_content and '>' in document_content:
            document_content = clean_html_content(document_content)
        
        # Use the LLM to analyze document flow if available
        if llm:
            prompt = f"""
            Analyze the flow and structure of this document:
            
            {document_content[:2000]}...
            
            Provide a brief analysis of:
            1. The logical flow of ideas
            2. How concise the writing is
            3. Three specific suggestions for improvement
            
            Format your response as JSON with keys: flow_analysis, conciseness, suggestions (array of 3 items)
            """
            
            try:
                result = llm(prompt)
                # Try to parse as JSON
                try:
                    analysis = json.loads(result)
                    return analysis
                except:
                    # Fallback to structured extraction if JSON parsing fails
                    flow_match = re.search(r'flow_analysis["\s:]+([^"]+)', result)
                    concise_match = re.search(r'conciseness["\s:]+([^"]+)', result)
                    suggestions = re.findall(r'suggestions[\s\S]*?["\[]([^"]+)', result)
                    
                    return {
                        "flow_analysis": flow_match.group(1) if flow_match else "The document has a reasonable structure.",
                        "conciseness": concise_match.group(1) if concise_match else "The document could be more concise.",
                        "suggestions": suggestions[:3] if suggestions else [
                            "Consider using more transition words between paragraphs",
                            "The introduction could be more concise",
                            "Try to reduce redundant phrases"
                        ]
                    }
            except Exception as e:
                print(f"Error using LLM for flow analysis: {str(e)}")
        
        # Fallback analysis
        return {
            "flow_analysis": "The document appears to have a logical structure with clear sections.",
            "conciseness": "Some paragraphs could be shortened for better readability.",
            "suggestions": [
                "Consider using more transition words between paragraphs",
                "The introduction could be more concise",
                "Try to reduce redundant phrases"
            ]
        }
    except Exception as e:
        print(f"Error in document flow analysis: {str(e)}")
        return {
            "flow_analysis": "Unable to analyze document flow due to an error.",
            "conciseness": "Unable to analyze conciseness due to an error.",
            "suggestions": ["Check document format", "Ensure document has sufficient content", "Try again with a different document"]
        }

def check_grammar(document_content):
    """Check for grammar issues"""
    
    try:
        # Clean HTML content if needed
        if '<' in document_content and '>' in document_content:
            document_content = clean_html_content(document_content)
        
        # Simple regex patterns for common grammar issues
        grammar_issues = []
        
        # Check for double spaces
        double_spaces = re.findall(r'  +', document_content)
        if double_spaces:
            grammar_issues.append({
                "type": "formatting",
                "issue": "Double spaces detected",
                "count": len(double_spaces)
            })
        
        # Check for common grammar mistakes (simplified)
        common_mistakes = [
            (r'\b(its|it\'s)\b', "Check usage of 'its' vs 'it's'"),
            (r'\b(there|their|they\'re)\b', "Check usage of 'there', 'their', or 'they're'"),
            (r'\b(your|you\'re)\b', "Check usage of 'your' vs 'you're'"),
            (r'\b(affect|effect)\b', "Check usage of 'affect' vs 'effect'"),
            (r'\b(then|than)\b', "Check usage of 'then' vs 'than'")
        ]
        
        for pattern, message in common_mistakes:
            if re.search(pattern, document_content):
                grammar_issues.append({
                    "type": "grammar",
                    "issue": message
                })
        
        # Check for sentence case issues
        sentences = re.findall(r'[.!?]\s+([a-z])', document_content)
        if sentences:
            grammar_issues.append({
                "type": "grammar",
                "issue": "Sentences should start with capital letters",
                "count": len(sentences)
            })
        
        return grammar_issues
    except Exception as e:
        print(f"Error in grammar check: {str(e)}")
        return [{
            "type": "error",
            "issue": "Unable to check grammar due to an error"
        }]

def suggest_vocabulary(document_content):
    """Suggest vocabulary improvements"""
    
    try:
        # Clean HTML content if needed
        if '<' in document_content and '>' in document_content:
            document_content = clean_html_content(document_content)
        
        # Simple word replacement suggestions
        common_words = {
            "good": ["excellent", "outstanding", "superb"],
            "bad": ["poor", "substandard", "inadequate"],
            "big": ["large", "substantial", "significant"],
            "small": ["tiny", "minute", "compact"],
            "said": ["stated", "mentioned", "noted"],
            "very": ["extremely", "exceedingly", "notably"],
            "a lot": ["numerous", "abundant", "plentiful"],
            "important": ["crucial", "essential", "vital"],
            "show": ["demonstrate", "illustrate", "exhibit"],
            "think": ["consider", "contemplate", "reflect"]
        }
        
        suggestions = []
        
        for word, replacements in common_words.items():
            pattern = r'\b' + word + r'\b'
            matches = re.findall(pattern, document_content, re.IGNORECASE)
            if matches:
                suggestions.append({
                    "original": word,
                    "count": len(matches),
                    "suggestions": replacements
                })
        
        return suggestions
    except Exception as e:
        print(f"Error in vocabulary suggestions: {str(e)}")
        return [{
            "original": "error",
            "suggestions": ["Unable to suggest vocabulary improvements due to an error"]
        }]

@app.route('/chat', methods=['POST'])
def chat():
    global qa_chain, document_content_cache
    
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400
    
    message = data.get('message', '')
    document_content = data.get('documentContent', '')
    
    # Initialize model if not already done
    if model is None or tokenizer is None:
        if not initialize_model():
            return jsonify({"response": "I'm sorry, I couldn't initialize the language model. Please try again later."}), 500
    
    # Create QA chain if not exists or document changed
    if (qa_chain is None or document_content_cache != document_content) and document_content:
        if not create_qa_chain(document_content):
            return jsonify({"response": "I'm sorry, I couldn't process your document. Please ensure it contains valid text content."}), 500
    
    try:
        # If it's a document analysis request
        if "analyze" in message.lower() or "critique" in message.lower() or "flow" in message.lower():
            flow_analysis = analyze_document_flow(document_content)
            grammar_issues = check_grammar(document_content)
            vocabulary_suggestions = suggest_vocabulary(document_content)
            
            response = {
                "response": f"""
                Here's my analysis of your document:
                
                Flow and Structure:
                {flow_analysis['flow_analysis']}
                {flow_analysis['conciseness']}
                
                Suggestions for improvement:
                - {flow_analysis['suggestions'][0]}
                - {flow_analysis['suggestions'][1]}
                - {flow_analysis['suggestions'][2]}
                
                Grammar check found {len(grammar_issues)} potential issues.
                
                Vocabulary enhancement:
                I found {len(vocabulary_suggestions)} words that could be replaced with more precise alternatives.
                
                Would you like more specific details about any part of this analysis?
                """
            }
            print(response)
        # For general questions about the document
        elif qa_chain and document_content:
            try:
                result = qa_chain({"query": message})
                response = {"response": result.get("result", "I couldn't find an answer to that question in the document.")}
            except Exception as e:
                print(f"Error in QA chain: {str(e)}")
                # Fallback to direct LLM response
                try:
                    prompt = f"""
                    Based on this document:
                    {document_content[:1000]}...
                    
                    Answer this question: {message}
                    """
                    result = llm(prompt)
                    response = {"response": result}
                except:
                    response = {"response": "I'm sorry, I couldn't process your question about the document. Please try asking in a different way."}
        else:
            response = {"response": "Please upload a document first so I can answer questions about it."}
            
        return jsonify(response)
    
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        return jsonify({"response": "I'm sorry, I encountered an error processing your request. Please try again."}), 500

@app.route('/analyze', methods=['POST'])
def analyze_document():
    data = request.json
    if not data or 'documentContent' not in data:
        return jsonify({"error": "No document content provided"}), 400
    
    document_content = data.get('documentContent', '')
    
    # Initialize model if not already done
    if model is None or tokenizer is None:
        if not initialize_model():
            return jsonify({"error": "Failed to initialize language model"}), 500
    
    try:
        flow_analysis = analyze_document_flow(document_content)
        grammar_issues = check_grammar(document_content)
        vocabulary_suggestions = suggest_vocabulary(document_content)
        
        return jsonify({
            "flow_analysis": flow_analysis,
            "grammar_issues": grammar_issues,
            "vocabulary_suggestions": vocabulary_suggestions
        })
    
    except Exception as e:
        print(f"Error analyzing document: {str(e)}")
        return jsonify({"error": "Failed to analyze document"}), 500

@app.route('/')
def index():
    return jsonify({"status": "RAG LLM Server is running"}), 200

if __name__ == '__main__':
    # Initialize model on startup
    initialize_model()
    app.run(host='0.0.0.0', port=5001)
