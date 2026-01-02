import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_openai_api_key():
    """Test that the OPENAI_API_KEY is working correctly."""
    
    # Get the API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("   Make sure you have a .env file with OPENAI_API_KEY set")
        return False
    
    print(f"✓ Found OPENAI_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make a test API call - simple completion
        print("\n🔍 Testing API connection with a simple chat completion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, API test successful!' if you can read this."}
            ],
            max_tokens=20
        )
        
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message.content
            print(f"✓ API call successful!")
            print(f"  Response: {message}")
            print(f"\n✅ OPENAI_API_KEY is working correctly!")
            return True
        else:
            print("⚠️  API call succeeded but no response received")
            return False
            
    except ImportError:
        print("❌ ERROR: OpenAI package not installed")
        print("   Run: pip install openai")
        return False
    except Exception as e:
        error_message = str(e)
        
        if "Incorrect API key" in error_message or "invalid_api_key" in error_message.lower():
            print(f"❌ ERROR: Invalid API key")
            print(f"   {error_message}")
            return False
        elif "rate_limit" in error_message.lower() or "quota" in error_message.lower():
            print(f"⚠️  WARNING: API rate limit or quota exceeded")
            print(f"   {error_message}")
            return False
        elif "insufficient_quota" in error_message.lower():
            print(f"❌ ERROR: Insufficient quota")
            print(f"   {error_message}")
            print(f"\n   Check your OpenAI account billing and quota at: https://platform.openai.com/usage")
            return False
        else:
            print(f"❌ ERROR: API call failed")
            print(f"   {error_message}")
            return False

if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI API Key Test")
    print("=" * 50)
    success = test_openai_api_key()
    print("=" * 50)
    
    if success:
        exit(0)
    else:
        exit(1)

