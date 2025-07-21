#!/usr/bin/env python3
import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def test_analysis_prompt():
    print("Testing the exact analysis prompt...")
    
    # Sample text from the inspection report
    sample_text = """
    PROPERTY INSPECTION REPORT
    Property Address: 123 Main Street, Anytown, USA
    Inspection Date: December 15, 2024
    Inspector: John Smith, Licensed Inspector #12345

    EXECUTIVE SUMMARY
    This residential property inspection reveals several significant issues requiring immediate attention. The property shows signs of deferred maintenance and has multiple safety concerns that should be addressed before occupancy.

    STRUCTURAL ASSESSMENT
    Foundation: The foundation shows multiple hairline cracks in the basement walls, particularly on the north side. These cracks are approximately 1/8 inch wide and extend vertically for 2-3 feet. While not immediately critical, they indicate potential settlement issues that should be monitored.

    ELECTRICAL SYSTEMS
    Main Panel: The electrical panel is outdated and appears to be at capacity. Several circuits are overloaded, and the panel lacks proper labeling. This poses a significant fire hazard and should be upgraded immediately.
    """
    
    prompt = f"""
    Analyze the following property inspection report and identify key risk factors. 
    Focus on structural, safety, electrical, plumbing, roofing, HVAC, and environmental issues.
    
    For each risk factor found, provide:
    1. Risk category
    2. Severity (Low/Medium/High/Critical)
    3. Description of the issue
    4. Recommended action
    5. Estimated cost impact (if mentioned)
    
    Report text:
    {sample_text}
    
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
    
    try:
        print("Making API call...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional property inspector and risk analyst. Provide accurate, detailed analysis of property inspection reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        print("✅ API call successful!")
        print(f"Response object: {response}")
        
        if response.choices and response.choices[0].message.content:
            response_text = response.choices[0].message.content.strip()
            print(f"Response text (first 500 chars): {response_text[:500]}...")
            
            # Clean up the response text - remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            print(f"Cleaned response text: {response_text[:500]}...")
            
            # Try to parse JSON
            try:
                parsed = json.loads(response_text)
                print("✅ JSON parsing successful!")
                print(f"Parsed data: {json.dumps(parsed, indent=2)}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Full response: {response_text}")
                return False
        else:
            print("❌ Empty response from API")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_analysis_prompt() 