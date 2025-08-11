import requests
import json

# Test the API endpoints
BASE_URL = "http://localhost:8000"

def test_root():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")

def test_create_ticket():
    """Test creating a ticket"""
    ticket_data = {
        "user_id": "test-user-123",
        "domain": "Travel",
        "summary": "My flight was cancelled and I need a refund",
        "priority": "high"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            headers={"Content-Type": "application/json"},
            data=json.dumps(ticket_data)
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ticket created: {result}")
            
            # Test retrieving the ticket
            ticket_id = result['ticket_id']
            get_response = requests.get(f"{BASE_URL}/api/tickets/{ticket_id}")
            if get_response.status_code == 200:
                print(f"✅ Ticket retrieved: {get_response.json()}")
            else:
                print(f"❌ Failed to retrieve ticket: {get_response.status_code}")
        else:
            print(f"❌ Failed to create ticket: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Create ticket failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Chatbot Ticket API...")
    print("=" * 50)
    
    test_root()
    print()
    test_create_ticket()
    print()
    print("🎉 Testing complete!") 