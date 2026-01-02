import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

def test_youtube_api_key():
    """Test that the YOUTUBE_API_KEY is working correctly."""
    
    # Get the API key from environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("❌ ERROR: YOUTUBE_API_KEY not found in environment variables")
        print("   Make sure you have a .env file with YOUTUBE_API_KEY set")
        return False
    
    print(f"✓ Found YOUTUBE_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize YouTube API client
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Make a test API call - search for a simple query
        print("\n🔍 Testing API connection with a simple search...")
        request = youtube.search().list(
            part='id,snippet',
            q='test',
            type='video',
            maxResults=1
        )
        response = request.execute()
        
        if response.get('items') and len(response['items']) > 0:
            video = response['items'][0]
            video_id = video['id']['videoId']
            video_title = video['snippet']['title']
            print(f"✓ API call successful!")
            print(f"  Found video: {video_title}")
            print(f"  Video ID: {video_id}")
            print(f"\n✅ YOUTUBE_API_KEY is working correctly!")
            return True
        else:
            print("⚠️  API call succeeded but no results returned")
            return False
            
    except Exception as e:
        error_message = str(e)
        
        if "API key not valid" in error_message or "invalid credentials" in error_message.lower():
            print(f"❌ ERROR: Invalid API key")
            print(f"   {error_message}")
            return False
        elif "accessNotConfigured" in error_message or "has not been used" in error_message or "is disabled" in error_message:
            print(f"❌ ERROR: YouTube Data API v3 is not enabled for your project")
            print(f"\n   To fix this:")
            print(f"   1. Visit: https://console.developers.google.com/apis/api/youtube.googleapis.com/overview")
            print(f"   2. Select your project (or create a new one)")
            print(f"   3. Click 'Enable' to enable YouTube Data API v3")
            print(f"   4. Wait a few minutes for changes to propagate")
            print(f"   5. Run this test again")
            print(f"\n   Error details: {error_message[:200]}...")
            return False
        elif "quota" in error_message.lower():
            print(f"⚠️  WARNING: API quota exceeded")
            print(f"   {error_message}")
            return False
        else:
            print(f"❌ ERROR: API call failed")
            print(f"   {error_message}")
            return False

if __name__ == "__main__":
    print("=" * 50)
    print("YouTube API Key Test")
    print("=" * 50)
    success = test_youtube_api_key()
    print("=" * 50)
    
    if success:
        exit(0)
    else:
        exit(1)

