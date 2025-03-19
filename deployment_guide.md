# Deployment Guide: Digital Front Desk with ESI Guidelines

This guide will walk you through setting up and deploying the Digital Front Desk system with ESI guidelines integration.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- An OpenAI API key
- ESI guidelines in PDF format

## Installation Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd digital-front-desk
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

   Activate the virtual environment:

   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:

   ```
   OPENAI_API_KEY=your_openai_api_key
   ESI_GUIDELINES_PATH=/absolute/path/to/esi_guidelines.pdf
   PORT=8000
   ```

## Testing the Knowledge Base

Before running the full application, you can test the ESI guidelines knowledge base:

```bash
python test_esi_knowledge_base.py --pdf /path/to/esi_guidelines.pdf
```

This will:
1. Load the PDF document
2. Process it into searchable chunks
3. Start an interactive session where you can input patient symptoms
4. Show what ESI guidelines would be retrieved
5. Simulate a triage response if OpenAI API key is configured

## Running the Application

Start the application with:

```bash
python -m digital_front_desk
```

By default, the application will run on port 8000 (or the PORT specified in your .env file).

## API Endpoints

The main API endpoints are:

- `POST /api/v1/message` - Send a patient message and get a triage response
- `GET /api/v1/queue` - View the current triage queue
- `GET /api/v1/health` - Check system health

## Production Deployment

For production deployment, consider:

1. **Using a production ASGI server**

   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker digital_front_desk.api:app
   ```

2. **Setting up behind a reverse proxy** (Nginx, Apache)

3. **Configuring proper logging**
   
   The application uses Python's logging module. Configure it appropriately for your environment.

4. **Monitoring**
   
   The application includes OpenTelemetry instrumentation for monitoring response times and errors.

## Troubleshooting

Common issues:

- **PDF Knowledge Base fails to initialize**
  
  Ensure the PDF path is correct and the file is accessible

- **OpenAI API errors**
  
  Check your API key and network connectivity

- **Memory usage issues with large PDFs**
  
  For very large ESI guideline documents, you may need to adjust the chunking parameters in `pdf_knowledge_base.py` 