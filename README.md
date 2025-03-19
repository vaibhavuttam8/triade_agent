# Digital Front Desk with ESI Guidelines

A medical triage system that uses AI to assess patient symptoms and provide appropriate guidance based on the Emergency Severity Index (ESI) triage algorithm.

## Features

- **AI-powered triage**: Assesses patient symptoms and determines appropriate ESI level
- **ESI Guidelines Integration**: Automatically references ESI guidelines from PDF documentation
- **Vector Search**: Uses FAISS to quickly find relevant information for patient symptoms
- **Multilevel Triage**: Categorizes patients into ESI levels 1-5
- **Queue Management**: Prioritizes patients based on urgency
- **Context Management**: Maintains conversation history for better assistance

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ESI_GUIDELINES_PATH=/path/to/esi_guidelines.pdf
   ```

3. Run the application:
   ```
   python -m digital_front_desk
   ```

## ESI Guidelines Integration

The system uses a PDF document containing ESI guidelines as a knowledge base:

1. **PDF Processing**: The document is processed at startup, extracting text and organizing it by headings
2. **Vector Embeddings**: Text is converted to numerical vectors using SentenceTransformer
3. **Fast Retrieval**: When a patient describes symptoms, the system quickly finds relevant guidelines
4. **AI Enhancement**: The found guidelines are provided to the AI to inform its response

## Emergency Severity Index (ESI) Levels

- **Level 1**: Immediate life-saving intervention required
  - Examples: Cardiac arrest, respiratory arrest, severe shock
  
- **Level 2**: High-risk situation or severe pain/distress
  - Examples: Chest pain, difficulty breathing, altered mental status
  
- **Level 3**: Multiple resources needed but stable condition
  - Examples: Abdominal pain requiring labs and imaging, fractures
  
- **Level 4**: One resource needed
  - Examples: Simple laceration, sprain, minor infection
  
- **Level 5**: No resources needed, lowest urgency
  - Examples: Minor cold symptoms, simple rash, medication refill

## System Components

- **Multi-Channel Interface**: Web Portal, Chat, Phone
- **AgentGPT Integration**: Processes initial inquiries and provides automated responses
- **Triage & Routing Engine**: Assesses patient symptoms and determines urgency
- **Conversation Context Management**: Maintains patient conversation history
- **Queue Management System**: Prioritizes cases based on medical urgency
- **Open Telemetry Integration**: Collects and analyzes performance metrics

## Project Structure

The project consists of two main components:

1. **Backend (digital_front_desk)**: A FastAPI application that handles inquiries, performs triage, and manages patient information
2. **Frontend (frontend)**: A React application that provides the web interface for patients

## Setup and Installation

### Backend

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Run the FastAPI server:

```bash
cd digital_front_desk
python -m uvicorn __main__:app --reload --port 8000
```

### Frontend

1. Install the required npm packages:

```bash
cd frontend
npm install
```

2. Run the React development server:

```bash
npm start
```

This will start the frontend on http://localhost:3000.

## Usage

1. Register an account on the web portal
2. Provide your basic health information (age, sex, allergies, etc.)
3. Describe your symptoms in the chat interface
4. The system will assess your symptoms, determine urgency, and provide appropriate guidance

## Security and Privacy

- User authentication is implemented using JWT tokens
- Patient information is kept confidential and is only used for healthcare purposes
- The system complies with healthcare data protection regulations

## Monitoring and Telemetry

The application uses Open Telemetry for monitoring and observability, tracking:

- Response times
- Triage decisions
- Queue metrics
- System health

## License

This project is licensed under the MIT License - see the LICENSE file for details. 