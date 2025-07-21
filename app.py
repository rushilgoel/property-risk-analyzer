import os
import json
import csv
import PyPDF2
import io
from flask import Flask, request, jsonify, render_template, send_file, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Risk categories and their keywords
RISK_CATEGORIES = {
    "Structural Issues": ["foundation", "crack", "settlement", "structural", "beam", "column", "load bearing"],
    "Electrical Hazards": ["electrical", "wiring", "outlet", "circuit", "breaker", "voltage", "amperage"],
    "Plumbing Problems": ["plumbing", "pipe", "leak", "water damage", "drain", "sewer", "mold"],
    "Roofing Issues": ["roof", "shingle", "gutter", "drainage", "water intrusion", "ceiling stain"],
    "HVAC Concerns": ["hvac", "heating", "cooling", "ventilation", "duct", "furnace", "ac"],
    "Safety Violations": ["safety", "code violation", "fire hazard", "smoke detector", "carbon monoxide"],
    "Environmental Hazards": ["asbestos", "lead", "radon", "mold", "water damage", "environmental"],
    "Accessibility Issues": ["accessibility", "ada", "ramp", "handrail", "door width", "bathroom"],
    "Property Condition": ["deferred maintenance", "wear", "deterioration", "age", "condition"]
}

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def analyze_risk_factors(text):
    """Use OpenAI to analyze and extract risk factors from text"""
    try:
        # Check if API key is set
        if not openai.api_key or openai.api_key == "your_openai_api_key_here":
            return {
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
                "risk_factors": [],
                "overall_risk_score": "Unknown",
                "summary": "API key not configured",
                "thinking_traces": []
            }
        
        # First, get thinking traces
        thinking_prompt = f"""
        Analyze the following property inspection report step by step. Think through each section carefully:

        Report text:
        {text[:4000]}

        For each major section (Structural, Electrical, Plumbing, etc.), provide your reasoning:
        1. What issues did you identify?
        2. Why are they concerning?
        3. What evidence supports your assessment?
        4. How severe do you think each issue is and why?

        Return your thinking process as a JSON array of reasoning steps:
        [
            {{
                "section": "string",
                "issues_found": ["string"],
                "reasoning": "string",
                "evidence": "string",
                "severity_assessment": "string"
            }}
        ]
        """
        
        print("Getting thinking traces...")
        thinking_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional property inspector. Think through each section methodically and explain your reasoning clearly."},
                {"role": "user", "content": thinking_prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        thinking_text = thinking_response.choices[0].message.content.strip()
        
        # Clean up thinking traces
        if thinking_text.startswith('```json'):
            thinking_text = thinking_text[7:]
        if thinking_text.startswith('```'):
            thinking_text = thinking_text[3:]
        if thinking_text.endswith('```'):
            thinking_text = thinking_text[:-3]
        
        thinking_text = thinking_text.strip()
        
        try:
            thinking_traces = json.loads(thinking_text)
        except json.JSONDecodeError:
            thinking_traces = [{"section": "Analysis", "reasoning": "Unable to parse thinking traces", "evidence": "JSON parsing error"}]
        
        # Now get the final analysis
        analysis_prompt = f"""
        Based on your analysis of the property inspection report, provide a comprehensive risk assessment.
        
        Report text:
        {text[:4000]}
        
        Return the analysis as a JSON object with this structure:
        {{
            "risk_factors": [
                {{
                    "category": "string",
                    "severity": "Low/Medium/High/Critical",
                    "description": "string",
                    "recommendation": "string",
                    "cost_impact": "string",
                    "location": "string"
                }}
            ],
            "overall_risk_score": "Low/Medium/High/Critical",
            "summary": "string"
        }}
        """
        
        print(f"Making API call with key: {openai.api_key[:10]}...")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional property inspector and risk analyst. Provide accurate, detailed analysis of property inspection reports."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        print(f"API Response received: {response}")
        
        if not response.choices or not response.choices[0].message.content:
            return {
                "error": "Empty response from OpenAI API",
                "risk_factors": [],
                "overall_risk_score": "Unknown",
                "summary": "API returned empty response",
                "thinking_traces": thinking_traces
            }
        
        response_text = response.choices[0].message.content.strip()
        print(f"Response text: {response_text[:200]}...")
        
        # Clean up the response text - remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith('```'):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        print(f"Cleaned response text: {response_text[:200]}...")
        
        # Try to parse JSON
        try:
            result = json.loads(response_text)
            result['thinking_traces'] = thinking_traces
            return result
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            print(f"Full response: {response_text}")
            
            # Fallback: create a basic analysis
            return {
                "error": f"Invalid JSON response from API: {json_error}",
                "risk_factors": [
                    {
                        "category": "Analysis Error",
                        "severity": "Medium",
                        "description": "Unable to parse AI response. Please check your API key and try again.",
                        "recommendation": "Verify OpenAI API key and ensure sufficient credits",
                        "cost_impact": "Unknown",
                        "location": "N/A"
                    }
                ],
                "overall_risk_score": "Unknown",
                "summary": "Analysis failed due to API response format issues",
                "thinking_traces": thinking_traces
            }
    
    except openai.error.AuthenticationError:
        return {
            "error": "OpenAI API authentication failed. Please check your API key.",
            "risk_factors": [],
            "overall_risk_score": "Unknown",
            "summary": "Authentication failed",
            "thinking_traces": []
        }
    except openai.error.RateLimitError:
        return {
            "error": "OpenAI API rate limit exceeded. Please try again later.",
            "risk_factors": [],
            "overall_risk_score": "Unknown",
            "summary": "Rate limit exceeded",
            "thinking_traces": []
        }
    except openai.error.APIError as api_error:
        return {
            "error": f"OpenAI API error: {str(api_error)}",
            "risk_factors": [],
            "overall_risk_score": "Unknown",
            "summary": f"API error: {str(api_error)}",
            "thinking_traces": []
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "error": f"Unexpected error analyzing text: {str(e)}",
            "risk_factors": [],
            "overall_risk_score": "Unknown",
            "summary": f"Analysis failed: {str(e)}",
            "thinking_traces": []
        }

def categorize_risks(risk_factors):
    """Categorize risks by severity and type"""
    categories = {
        "Critical": [],
        "High": [],
        "Medium": [],
        "Low": []
    }
    
    for risk in risk_factors:
        severity = risk.get('severity', 'Medium')
        if severity in categories:
            categories[severity].append(risk)
    
    return categories

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file)
        else:
            # Assume text file
            text = file.read().decode('utf-8')
        
        # Analyze the text
        analysis = analyze_risk_factors(text)
        
        # Add metadata
        analysis['filename'] = filename
        analysis['upload_time'] = datetime.now().isoformat()
        analysis['text_length'] = len(text)
        
        return jsonify(analysis)

@app.route('/stream-analysis', methods=['POST'])
def stream_analysis():
    """Stream the analysis process in real-time"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    def generate():
        try:
            filename = secure_filename(file.filename)
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting analysis...'})}\n\n"
            
            # Extract text based on file type
            if filename.lower().endswith('.pdf'):
                yield f"data: {json.dumps({'type': 'status', 'message': 'Extracting text from PDF...'})}\n\n"
                text = extract_text_from_pdf(file)
            else:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Reading text file...'})}\n\n"
                text = file.read().decode('utf-8')
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Document processed. Length: {len(text)} characters'})}\n\n"
            
            # Start thinking process
            yield f"data: {json.dumps({'type': 'thinking_start', 'message': 'Beginning AI analysis...'})}\n\n"
            
            # Get thinking traces with streaming
            thinking_traces = []
            sections = [
                "Structural Assessment",
                "Electrical Systems", 
                "Plumbing Systems",
                "HVAC Systems",
                "Safety Concerns",
                "Environmental Issues",
                "Accessibility",
                "Property Condition"
            ]
            
            for i, section in enumerate(sections):
                # Send thinking start for this section
                yield f"data: {json.dumps({'type': 'thinking_section', 'section': section, 'message': f'Analyzing {section}...'})}\n\n"
                
                # Analyze this section
                thinking_prompt = f"""
                Analyze the {section} section of this property inspection report:
                
                Report text:
                {text[:3000]}
                
                Focus specifically on {section}. Think through:
                1. What issues did you identify in this section?
                2. Why are they concerning?
                3. What evidence supports your assessment?
                4. How severe do you think each issue is and why?
                
                Return your analysis as JSON:
                {{
                    "section": "{section}",
                    "issues_found": ["issue1", "issue2"],
                    "reasoning": "detailed reasoning",
                    "evidence": "specific evidence from text",
                    "severity_assessment": "severity level and explanation"
                }}
                """
                
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a professional property inspector. Analyze each section methodically."},
                            {"role": "user", "content": thinking_prompt}
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    
                    # Clean up response
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]
                    if response_text.startswith('```'):
                        response_text = response_text[3:]
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]
                    
                    response_text = response_text.strip()
                    
                    try:
                        trace = json.loads(response_text)
                        thinking_traces.append(trace)
                        
                        # Send thinking result for this section
                        yield f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n"
                        
                    except json.JSONDecodeError:
                        trace = {
                            "section": section,
                            "issues_found": ["Analysis error"],
                            "reasoning": "Unable to parse AI response",
                            "evidence": "JSON parsing error",
                            "severity_assessment": "Unknown"
                        }
                        thinking_traces.append(trace)
                        yield f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n"
                        
                except Exception as e:
                    trace = {
                        "section": section,
                        "issues_found": ["API error"],
                        "reasoning": f"Error: {str(e)}",
                        "evidence": "API call failed",
                        "severity_assessment": "Unknown"
                    }
                    thinking_traces.append(trace)
                    yield f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n"
                
                # Small delay to make streaming visible
                time.sleep(0.5)
            
            # Get final analysis
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating final risk assessment...'})}\n\n"
            
            analysis = get_final_analysis(text)
            analysis['thinking_traces'] = thinking_traces
            analysis['filename'] = filename
            analysis['upload_time'] = datetime.now().isoformat()
            analysis['text_length'] = len(text)
            
            yield f"data: {json.dumps({'type': 'complete', 'data': analysis})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

def get_thinking_traces_streaming(text, yield_func):
    """Get thinking traces with real-time streaming"""
    sections = [
        "Structural Assessment",
        "Electrical Systems", 
        "Plumbing Systems",
        "HVAC Systems",
        "Safety Concerns",
        "Environmental Issues",
        "Accessibility",
        "Property Condition"
    ]
    
    thinking_traces = []
    
    for i, section in enumerate(sections):
        # Send thinking start for this section
        yield_func(f"data: {json.dumps({'type': 'thinking_section', 'section': section, 'message': f'Analyzing {section}...'})}\n\n")
        
        # Simulate thinking process for this section
        thinking_prompt = f"""
        Analyze the {section} section of this property inspection report:
        
        Report text:
        {text[:3000]}
        
        Focus specifically on {section}. Think through:
        1. What issues did you identify in this section?
        2. Why are they concerning?
        3. What evidence supports your assessment?
        4. How severe do you think each issue is and why?
        
        Return your analysis as JSON:
        {{
            "section": "{section}",
            "issues_found": ["issue1", "issue2"],
            "reasoning": "detailed reasoning",
            "evidence": "specific evidence from text",
            "severity_assessment": "severity level and explanation"
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional property inspector. Analyze each section methodically."},
                    {"role": "user", "content": thinking_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                trace = json.loads(response_text)
                thinking_traces.append(trace)
                
                # Send thinking result for this section
                yield_func(f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n")
                
            except json.JSONDecodeError:
                trace = {
                    "section": section,
                    "issues_found": ["Analysis error"],
                    "reasoning": "Unable to parse AI response",
                    "evidence": "JSON parsing error",
                    "severity_assessment": "Unknown"
                }
                thinking_traces.append(trace)
                yield_func(f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n")
                
        except Exception as e:
            trace = {
                "section": section,
                "issues_found": ["API error"],
                "reasoning": f"Error: {str(e)}",
                "evidence": "API call failed",
                "severity_assessment": "Unknown"
            }
            thinking_traces.append(trace)
            yield_func(f"data: {json.dumps({'type': 'thinking_result', 'section': section, 'trace': trace})}\n\n")
        
        # Small delay to make streaming visible
        time.sleep(0.5)
    
    return thinking_traces

def get_final_analysis(text):
    """Get the final risk assessment"""
    analysis_prompt = f"""
    Based on your analysis of the property inspection report, provide a comprehensive risk assessment.
    
    Report text:
    {text[:4000]}
    
    Return the analysis as a JSON object with this structure:
    {{
        "risk_factors": [
            {{
                "category": "string",
                "severity": "Low/Medium/High/Critical",
                "description": "string",
                "recommendation": "string",
                "cost_impact": "string",
                "location": "string"
            }}
        ],
        "overall_risk_score": "Low/Medium/High/Critical",
        "summary": "string"
    }}
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional property inspector and risk analyst. Provide accurate, detailed analysis of property inspection reports."},
            {"role": "user", "content": analysis_prompt}
        ],
        max_tokens=1500,
        temperature=0.3
    )
    
    response_text = response.choices[0].message.content.strip()
    
    # Clean up response
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "risk_factors": [],
            "overall_risk_score": "Unknown",
            "summary": "Analysis failed"
        }

@app.route('/export', methods=['POST'])
def export_report():
    data = request.json
    
    # Create CSV report
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Risk Analysis Report'])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Filename:', data.get('filename', 'Unknown')])
    writer.writerow(['Overall Risk Score:', data.get('overall_risk_score', 'Unknown')])
    writer.writerow(['Total Risk Factors:', len(data.get('risk_factors', []))])
    writer.writerow([])
    
    # Write summary
    if data.get('summary'):
        writer.writerow(['Summary'])
        writer.writerow([data['summary']])
        writer.writerow([])
    
    # Write risk factors
    if data.get('risk_factors'):
        writer.writerow(['Risk Factors'])
        writer.writerow(['Category', 'Severity', 'Description', 'Recommendation', 'Cost Impact', 'Location'])
        
        for risk in data['risk_factors']:
            writer.writerow([
                risk.get('category', ''),
                risk.get('severity', ''),
                risk.get('description', ''),
                risk.get('recommendation', ''),
                risk.get('cost_impact', ''),
                risk.get('location', '')
            ])
    
    # Write thinking traces
    if data.get('thinking_traces'):
        writer.writerow([])
        writer.writerow(['AI Analysis Process'])
        writer.writerow(['Section', 'Issues Found', 'Reasoning', 'Evidence', 'Severity Assessment'])
        
        for trace in data['thinking_traces']:
            issues = '; '.join(trace.get('issues_found', [])) if trace.get('issues_found') else ''
            writer.writerow([
                trace.get('section', ''),
                issues,
                trace.get('reasoning', ''),
                trace.get('evidence', ''),
                trace.get('severity_assessment', '')
            ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001) 