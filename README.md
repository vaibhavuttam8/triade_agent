# Digital Front Desk & Triage Agent

An AI-powered system designed to handle initial patient inquiries across multiple channels, implement smart triage logic, and efficiently route urgent cases. The system integrates OpenAI's GPT models for intelligent responses and OpenTelemetry for comprehensive monitoring and observability.

## Features

- Multi-channel support (Phone, Chat, Web Portal)
- Intelligent triage system with urgency assessment
- Automated response generation for common inquiries
- Priority-based queue management
- Conversation context management
- Comprehensive telemetry and monitoring
- RESTful API interface

## Requirements

- Python 3.8+
- OpenAI API key
- OpenTelemetry collector (for metrics and tracing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/digital-front-desk.git
cd digital-front-desk
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the service:
```bash
python -m digital_front_desk
```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### Process Patient Inquiry
```
POST /inquiries
```
Process a new patient inquiry through any supported channel.

### Queue Management
```
GET /queue/status
POST /queue/next
DELETE /queue/{user_id}
```
Manage the patient queue and retrieve queue status.

### Context Management
```
GET /context/{user_id}
```
Retrieve conversation context for a specific user.

## Monitoring

The system uses OpenTelemetry for monitoring and observability. Key metrics include:

- Request processing times
- Queue sizes and wait times
- Triage scores distribution
- AI model performance
- Conversation context statistics

## Configuration

The system can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OTLP_ENDPOINT`: OpenTelemetry collector endpoint
- `MODEL_NAME`: GPT model to use (default: gpt-4-turbo-preview)
- `PORT`: Server port (default: 8000)

## Architecture

The system consists of several key components:

1. **Agent Processor**: Coordinates AI responses and triage decisions
2. **Triage Engine**: Assesses urgency and routes cases
3. **Queue Manager**: Handles priority-based queuing
4. **Context Manager**: Maintains conversation history
5. **Telemetry Manager**: Handles monitoring and metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 