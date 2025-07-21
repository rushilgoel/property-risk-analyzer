#!/usr/bin/env python3
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def test_api():
    print("Testing OpenAI API connection...")
    print(f"API Key (first 10 chars): {openai.api_key[:10] if openai.api_key else 'NOT SET'}...")
    
    try:
        # Simple test call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, API is working!' in JSON format: {\"message\": \"Hello, API is working!\"}"}
            ],
            max_tokens=50
        )
        
        print("✅ API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except openai.error.AuthenticationError:
        print("❌ Authentication failed. Please check your API key.")
        return False
    except openai.error.RateLimitError:
        print("❌ Rate limit exceeded. Please try again later.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_api() 