#!/usr/bin/env python3
"""
This script allows testing the ESI guidelines knowledge base functionality.
It loads the knowledge base and allows users to enter patient symptoms to see
what guidelines would be retrieved and how they would influence triage.
"""

import os
import sys
from dotenv import load_dotenv
import argparse
from digital_front_desk.pdf_knowledge_base import PDFKnowledgeBase
import openai

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Test ESI Guidelines Knowledge Base")
    parser.add_argument("--pdf", help="Path to ESI guidelines PDF", default=os.getenv("ESI_GUIDELINES_PATH", "esi_guidelines.pdf"))
    parser.add_argument("--test", help="Run with a predefined test case", action="store_true")
    args = parser.parse_args()

    # Initialize knowledge base
    kb = PDFKnowledgeBase()
    kb.pdf_path = args.pdf
    
    print(f"Initializing knowledge base from: {kb.pdf_path}")
    success = kb.initialize()
    
    if not success:
        print(f"Failed to initialize knowledge base. Make sure the PDF file exists at: {kb.pdf_path}")
        sys.exit(1)
    
    print(f"Knowledge base initialized successfully with {len(kb.chunks)} chunks.")

    # OpenAI client for simulating AI response
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY not set. Simulated AI response will not be available.")
        client = None
    else:
        client = openai.OpenAI(api_key=openai_api_key)
    
    # Run a predefined test case
    if args.test:
        test_symptoms = [
            "I'm experiencing severe chest pain and shortness of breath",
            "My child has a mild fever and runny nose",
            "I cut my finger while cooking and it might need stitches",
            "I've been having severe abdominal pain and vomiting for 2 days",
            "I twisted my ankle and it's swollen"
        ]
        
        for symptom in test_symptoms:
            print("\n" + "="*80)
            print(f"TEST CASE: {symptom}")
            process_symptoms(kb, symptom, client)
            input("Press Enter to continue to the next test case...")
    
    # Interactive mode
    else:
        print("\nEnter patient symptoms to query the knowledge base (type 'exit' to quit):")
        while True:
            symptoms = input("\nPatient symptoms: ")
            if symptoms.lower() in ['exit', 'quit', 'q']:
                break
            
            process_symptoms(kb, symptoms, client)

def process_symptoms(kb, symptoms, client):
    # Get relevant context from knowledge base
    print("\nQuerying knowledge base...")
    context = kb.get_context_for_symptoms(symptoms)
    
    print(f"\nRetrieved {context.count('\\n\\n')+1} relevant sections from ESI guidelines:")
    print("-" * 40)
    print(context)
    print("-" * 40)
    
    # If OpenAI client is available, simulate AI response
    if client:
        print("\nSimulating AI response with retrieved ESI guidelines...")
        
        system_prompt = """You are a medical triage assistant using the Emergency Severity Index (ESI).
Based on the patient's symptoms and the provided ESI guidelines, determine:
1. The appropriate ESI level (1-5)
2. The recommended action
3. The resources likely needed

Format your response as:
ESI LEVEL: [1-5]
RECOMMENDED ACTION: [action]
RESOURCES NEEDED: [resources]
REASONING: [brief explanation]
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Reference these ESI guidelines:\n\n{context}"},
                {"role": "user", "content": f"Patient symptoms: {symptoms}"}
            ]
        )
        
        print("\nSimulated Triage Response:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)

if __name__ == "__main__":
    main() 