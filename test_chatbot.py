#!/usr/bin/env python3
"""
Test script for the Customer Support Chatbot
Tests the complete flow from frontend to backend
"""

import asyncio
import json
import sys
from datetime import datetime
import aiohttp

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

class ChatbotTester:
    def __init__(self):
        self.session = None
        self.conversation_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_backend_health(self):
        """Test if backend is running"""
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend is running: {data.get('message', 'OK')}")
                    return True
                else:
                    print(f"❌ Backend returned status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
    
    async def test_domains_endpoint(self):
        """Test the domains endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL}/domains") as response:
                if response.status == 200:
                    data = await response.json()
                    domains = data.get('domains', [])
                    print(f"✅ Domains endpoint working: {len(domains)} domains available")
                    for domain in domains[:3]:  # Show first 3 domains
                        print(f"   - {domain['name']}: {domain['description'][:50]}...")
                    return True
                else:
                    print(f"❌ Domains endpoint returned status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Domains endpoint test failed: {e}")
            return False
    
    async def test_chat_endpoint(self):
        """Test the chat endpoint"""
        try:
            test_query = {
                "user_id": "test_user_123",
                "domain": "Healthcare",
                "question": "What are the common symptoms of a cold?"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/ask",
                json=test_query,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.conversation_id = data.get('conversation_id')
                    answer = data.get('answer', '')
                    print(f"✅ Chat endpoint working")
                    print(f"   Conversation ID: {self.conversation_id}")
                    print(f"   AI Response: {answer[:100]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Chat endpoint returned status {response.status}: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Chat endpoint test failed: {e}")
            return False
    
    async def test_conversation_history(self):
        """Test conversation history retrieval"""
        if not self.conversation_id:
            print("❌ No conversation ID available for history test")
            return False
        
        try:
            async with self.session.get(f"{BACKEND_URL}/conversation/{self.conversation_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    message_count = data.get('message_count', 0)
                    print(f"✅ Conversation history working: {message_count} messages")
                    return True
                else:
                    print(f"❌ Conversation history returned status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Conversation history test failed: {e}")
            return False
    
    async def test_multiple_domains(self):
        """Test chat with multiple domains"""
        domains_to_test = [
            ("Education", "How can AI help in personalized learning?"),
            ("Finance", "What are the basics of investing?"),
            ("Technology", "What is machine learning?")
        ]
        
        success_count = 0
        for domain, question in domains_to_test:
            try:
                test_query = {
                    "user_id": "test_user_123",
                    "domain": domain,
                    "question": question
                }
                
                async with self.session.post(
                    f"{BACKEND_URL}/ask",
                    json=test_query,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        answer = data.get('answer', '')
                        print(f"✅ {domain} domain working: {answer[:50]}...")
                        success_count += 1
                    else:
                        print(f"❌ {domain} domain failed with status {response.status}")
            except Exception as e:
                print(f"❌ {domain} domain test failed: {e}")
        
        print(f"✅ Multiple domains test: {success_count}/{len(domains_to_test)} domains working")
        return success_count == len(domains_to_test)
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Chatbot Integration Tests")
        print("=" * 50)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Domains Endpoint", self.test_domains_endpoint),
            ("Chat Endpoint", self.test_chat_endpoint),
            ("Conversation History", self.test_conversation_history),
            ("Multiple Domains", self.test_multiple_domains)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name}...")
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
            except Exception as e:
                print(f"❌ {test_name} test error: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your chatbot is ready to use.")
            print("\n📋 Next steps:")
            print("1. Start the frontend: npm run dev")
            print("2. Visit http://localhost:5173")
            print("3. Select a domain and start chatting!")
        else:
            print("⚠️  Some tests failed. Please check the errors above.")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure all services are running (Redis, MongoDB, PostgreSQL)")
            print("2. Check your .env file has the correct GEMINI_API_KEY")
            print("3. Verify the backend is running on port 8000")
        
        return passed == total

async def main():
    """Main test function"""
    async with ChatbotTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)
