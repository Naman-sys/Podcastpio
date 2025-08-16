#!/usr/bin/env python3
"""
Comprehensive test suite for PodcastAI Streamlit Application
Tests all core functionality to ensure everything works properly
"""

import sys
import os
import json
import requests
from unittest.mock import patch, MagicMock

def test_imports():
    """Test all required imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit import: OK")
        
        import google.generativeai as genai
        print("✅ Google Generative AI import: OK")
        
        import openai
        print("✅ OpenAI import: OK")
        
        import requests
        print("✅ Requests import: OK")
        
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup import: OK")
        
        from dotenv import load_dotenv
        print("✅ Python-dotenv import: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_podcast_generator_class():
    """Test PodcastScriptGenerator class functionality"""
    print("\n🔍 Testing PodcastScriptGenerator class...")
    
    try:
        # Import the class from our app
        sys.path.append('.')
        from streamlit_app import PodcastScriptGenerator
        
        # Initialize generator
        generator = PodcastScriptGenerator()
        print("✅ Generator initialization: OK")
        
        # Test sample content
        test_content = """
        Artificial Intelligence has revolutionized the way we approach technology and business. 
        Companies are now leveraging AI to automate processes, enhance customer experiences, 
        and drive innovation across various industries. Machine learning algorithms can analyze 
        vast amounts of data in real-time, providing insights that were previously impossible 
        to obtain. This technological advancement is reshaping the future of work and creating 
        new opportunities for businesses to grow and adapt in an increasingly digital world.
        """
        
        # Test fallback script generation
        script = generator.generate_fallback_script(
            content=test_content.strip(),
            style="professional",
            duration="10-20", 
            show_name="Tech Talk Today"
        )
        
        # Verify script structure
        required_keys = ["intro", "mainContent", "outro", "showNotes"]
        for key in required_keys:
            if key not in script:
                print(f"❌ Missing key in script: {key}")
                return False
            
        print("✅ Fallback script generation: OK")
        
        # Verify show notes structure
        show_notes = script["showNotes"]
        required_notes_keys = ["keyTopics", "resources", "timestamps", "episodeDetails"]
        for key in required_notes_keys:
            if key not in show_notes:
                print(f"❌ Missing key in show notes: {key}")
                return False
                
        print("✅ Show notes structure: OK")
        
        # Test content length
        if len(script["intro"]) < 50:
            print("❌ Intro too short")
            return False
            
        if len(script["mainContent"]) < 100:
            print("❌ Main content too short") 
            return False
            
        if len(script["outro"]) < 50:
            print("❌ Outro too short")
            return False
            
        print("✅ Content length validation: OK")
        
        # Test different styles
        styles = ["conversational", "professional", "educational", "interview"]
        for style in styles:
            test_script = generator.generate_fallback_script(
                content=test_content.strip(),
                style=style,
                duration="10-20"
            )
            if "intro" not in test_script:
                print(f"❌ Style {style} failed")
                return False
                
        print("✅ All podcast styles: OK")
        
        # Test different durations
        durations = ["5-10", "10-20", "20-30", "30+"]
        for duration in durations:
            test_script = generator.generate_fallback_script(
                content=test_content.strip(),
                style="conversational",
                duration=duration
            )
            if "showNotes" not in test_script:
                print(f"❌ Duration {duration} failed")
                return False
                
        print("✅ All duration options: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Generator class test failed: {e}")
        return False

def test_url_extraction():
    """Test URL content extraction functionality"""
    print("\n🔍 Testing URL extraction...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        
        # Mock a successful HTTP response
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>AI Revolution in Business</h1>
                    <p>Artificial intelligence is transforming how businesses operate in the modern world. 
                    Companies are implementing AI solutions to streamline operations, enhance customer 
                    service, and gain competitive advantages in their respective markets.</p>
                    <p>The integration of machine learning algorithms has enabled organizations to 
                    process large datasets efficiently and extract valuable insights for strategic 
                    decision-making processes.</p>
                </article>
            </body>
        </html>
        """
        
        # Mock requests.get
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.content = mock_html.encode('utf-8')
            mock_get.return_value = mock_response
            
            result = generator.extract_content_from_url("https://example.com/test")
            
            # Verify result structure
            required_fields = ["title", "content", "word_count"]
            for field in required_fields:
                if field not in result:
                    print(f"❌ Missing field in URL extraction: {field}")
                    return False
                    
            if result["word_count"] < 10:
                print("❌ URL extraction - insufficient word count")
                return False
                
            print("✅ URL content extraction: OK")
            return True
            
    except Exception as e:
        print(f"❌ URL extraction test failed: {e}")
        return False

def test_content_analysis():
    """Test content analysis and topic extraction"""
    print("\n🔍 Testing content analysis...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        
        # Test technology content
        tech_content = """
        Machine learning and artificial intelligence are revolutionizing software development. 
        Companies are using neural networks and deep learning algorithms to create innovative 
        applications. Python programming and data science have become essential skills for 
        modern developers working with AI technologies.
        """
        
        script = generator.generate_fallback_script(
            content=tech_content,
            style="educational", 
            duration="10-20"
        )
        
        # Check if technology category was detected
        category = script["showNotes"]["episodeDetails"]["category"]
        if category != "Technology":
            print(f"❌ Expected Technology category, got: {category}")
            return False
            
        print("✅ Technology content categorization: OK")
        
        # Test business content
        business_content = """
        The economy is experiencing significant changes as companies adapt to new market conditions. 
        Financial strategies and business models are evolving to meet customer demands. Revenue 
        growth and market analysis have become critical for organizational success in competitive industries.
        """
        
        script = generator.generate_fallback_script(
            content=business_content,
            style="professional",
            duration="20-30"
        )
        
        category = script["showNotes"]["episodeDetails"]["category"]
        if category != "Business":
            print(f"❌ Expected Business category, got: {category}")
            return False
            
        print("✅ Business content categorization: OK")
        
        # Test key topics extraction
        key_topics = script["showNotes"]["keyTopics"]
        if len(key_topics) == 0:
            print("❌ No key topics extracted")
            return False
            
        print("✅ Key topics extraction: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Content analysis test failed: {e}")
        return False

def test_script_structure():
    """Test generated script structure and formatting"""
    print("\n🔍 Testing script structure...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        
        test_content = """
        Climate change represents one of the most pressing challenges of our time. 
        Scientists worldwide are researching innovative solutions to reduce carbon emissions 
        and develop sustainable technologies. Renewable energy sources like solar and wind 
        power are becoming increasingly efficient and cost-effective alternatives to fossil fuels.
        """
        
        script = generator.generate_fallback_script(
            content=test_content,
            style="conversational",
            duration="15-20",
            show_name="Climate Conversations"
        )
        
        # Test intro contains music cues
        intro = script["intro"]
        if "[INTRO MUSIC" not in intro:
            print("❌ Intro missing music cues")
            return False
            
        if "Climate Conversations" not in intro:
            print("❌ Show name not in intro")
            return False
            
        print("✅ Intro structure and formatting: OK")
        
        # Test main content has transitions
        main_content = script["mainContent"]
        if "[TRANSITION MUSIC" not in main_content:
            print("❌ Main content missing transition cues")
            return False
            
        print("✅ Main content transitions: OK")
        
        # Test outro structure
        outro = script["outro"]
        if "[OUTRO MUSIC" not in outro:
            print("❌ Outro missing music cues")
            return False
            
        if "Climate Conversations" not in outro:
            print("❌ Show name not in outro")
            return False
            
        print("✅ Outro structure: OK")
        
        # Test timestamps are logical
        timestamps = script["showNotes"]["timestamps"]
        if len(timestamps) < 3:
            print("❌ Insufficient timestamps")
            return False
            
        # Check timestamp format
        for ts in timestamps:
            if ":" not in ts["time"]:
                print(f"❌ Invalid timestamp format: {ts['time']}")
                return False
                
        print("✅ Timestamp structure: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Script structure test failed: {e}")
        return False

def test_api_fallback():
    """Test API fallback functionality"""
    print("\n🔍 Testing API fallback system...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        
        # Test with no API keys (should use fallback)
        with patch.dict(os.environ, {}, clear=True):
            generator = PodcastScriptGenerator()
            
            test_content = "This is a test article about renewable energy and sustainable development."
            
            # This should use fallback since no API keys
            script = generator.generate_script(
                content=test_content,
                style="educational",
                duration="10-20",
                show_name="Green Tech Weekly"
            )
            
            if "intro" not in script:
                print("❌ Fallback generation failed")
                return False
                
            print("✅ API fallback system: OK")
            
        return True
        
    except Exception as e:
        print(f"❌ API fallback test failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🔍 Testing edge cases...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        
        # Test very short content
        short_content = "AI is good."
        script = generator.generate_fallback_script(
            content=short_content,
            style="conversational", 
            duration="5-10"
        )
        
        if "intro" not in script:
            print("❌ Short content handling failed")
            return False
            
        print("✅ Short content handling: OK")
        
        # Test empty show name
        script = generator.generate_fallback_script(
            content="Technology is advancing rapidly in many sectors.",
            style="professional",
            duration="10-20",
            show_name=""
        )
        
        # The function has "The Show" as default parameter, so empty string should still use "The Show"
        if "The Show" not in script["intro"]:
            print("❌ Default show name fallback failed")
            print(f"Expected 'The Show' in intro, but got: {script['intro'][:100]}...")
            return False
            
        print("✅ Default show name handling: OK")
        
        # Test unknown style (should default)
        script = generator.generate_fallback_script(
            content="Business trends are changing constantly.",
            style="unknown_style",
            duration="10-20"
        )
        
        if "intro" not in script:
            print("❌ Unknown style handling failed") 
            return False
            
        print("✅ Unknown style handling: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        return False

def test_export_functionality():
    """Test script export and formatting"""
    print("\n🔍 Testing export functionality...")
    
    try:
        from streamlit_app import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        
        script = generator.generate_fallback_script(
            content="Digital transformation is reshaping business operations globally.",
            style="professional",
            duration="10-20",
            show_name="Digital Insights"
        )
        
        # Create export text format
        show_notes = script["showNotes"]
        export_text = f"""# Digital Insights

## Intro
{script['intro']}

## Main Content
{script['mainContent']}

## Outro  
{script['outro']}

## Show Notes
### Key Topics
{chr(10).join(['• ' + topic for topic in show_notes['keyTopics']])}
"""
        
        if len(export_text) < 200:
            print("❌ Export text too short")
            return False
            
        if "Digital Insights" not in export_text:
            print("❌ Show name not in export")
            return False
            
        print("✅ Export formatting: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Export functionality test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting comprehensive test suite for PodcastAI...")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Generator Class", test_podcast_generator_class),
        ("URL Extraction", test_url_extraction),
        ("Content Analysis", test_content_analysis),
        ("Script Structure", test_script_structure),
        ("API Fallback", test_api_fallback),
        ("Edge Cases", test_edge_cases),
        ("Export Function", test_export_functionality)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Your PodcastAI app is working perfectly!")
    else:
        print(f"⚠️  {failed} tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)