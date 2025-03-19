import asyncio
import aiohttp
import json
import time

async def test_traces():
    async with aiohttp.ClientSession() as session:
        # Test 1: Register a new user
        print("Test 1: Registering new user...")
        register_data = {
            "username": f"test_user_{int(time.time())}",
            "password": "test123"
        }
        async with session.post(
            "http://localhost:8000/register",
            data=register_data
        ) as response:
            result = await response.json()
            user_id = result.get("user_id")
            print(f"Registration response: {result}")

        # Test 2: Login
        print("\nTest 2: Logging in...")
        login_data = {
            "username": register_data["username"],
            "password": register_data["password"]
        }
        async with session.post(
            "http://localhost:8000/token",
            data=login_data
        ) as response:
            result = await response.json()
            token = result.get("access_token")
            print(f"Login successful, got token")

        headers = {"Authorization": f"Bearer {token}"}

        # Test 3: Update patient info
        print("\nTest 3: Updating patient info...")
        patient_info = {
            "user_id": user_id,
            "full_name": "Test Patient",
            "date_of_birth": "1990-01-01",
            "sex": "M",
            "contact_number": "+1234567890",
            "medical_history": ["Asthma"],
            "current_medications": ["Ventolin"],
            "allergies": ["Peanuts"],
            "emergency_contact": {
                "name": "Emergency Contact",
                "relationship": "Spouse",
                "phone": "+0987654321"
            }
        }
        async with session.post(
            "http://localhost:8000/patient-info",
            headers=headers,
            json=patient_info
        ) as response:
            result = await response.json()
            print(f"Patient info update response: {result}")

        # Test 4: Send multiple inquiries
        print("\nTest 4: Sending inquiries...")
        inquiries = [
            "I have a severe headache and fever",
            "When is the next available appointment?",
            "I need a prescription refill for my asthma medication"
        ]

        for inquiry in inquiries:
            inquiry_data = {
                "channel_type": "web_portal",
                "message": inquiry,
                "user_id": user_id,
                "patient_info": patient_info
            }
            async with session.post(
                "http://localhost:8000/inquiries",
                headers=headers,
                json=inquiry_data
            ) as response:
                result = await response.json()
                print(f"Inquiry response for '{inquiry[:30]}...': {result.get('response')[:50]}...")
            await asyncio.sleep(1)  # Small delay between requests

if __name__ == "__main__":
    asyncio.run(test_traces()) 