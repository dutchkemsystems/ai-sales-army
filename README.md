# AI Sales Army - Multi-Agent Sales Automation Platform

A complete multi-agent AI sales automation system built by Dutchkem Ventures. Uses 7 specialized AI agents working in sequence to find, research, engage, and convert leads into booked meetings.

## The 7-Agent Pipeline

| Agent | Function |
|-------|----------|
| **Lead Finder** | Discovers prospects across LinkedIn, Apollo, Twitter |
| **Researcher** | Deep company & individual research |
| **Personalizer** | Creates hyper-personalized outreach messages |
| **Outreach** | Executes multi-channel campaigns (Email, LinkedIn, SMS, Twitter) |
| **Follow-Up** | Intelligent follow-up sequences until response |
| **Appointment Setter** | BANT qualification & meeting booking |
| **Sales Manager** | Pipeline analytics, forecasting & recommendations |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, LangChain, OpenAI GPT-4
- **Database**: PostgreSQL, Redis, Elasticsearch
- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts
- **Integrations**: SendGrid, LinkedIn, Apollo, Clearbit, Twilio, Google Calendar

## Quick Start

```bash
# Clone
git clone https://github.com/your-org/ai-sales-army.git
cd ai-sales-army

# Configure
cp backend/.env.example backend/.env
# Add your API keys

# Run with Docker
docker-compose up -d

# Access
open http://localhost:3000
```

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /api/leads/discover` - Start lead discovery
- `GET /api/leads` - List all leads
- `GET /api/analytics/pipeline` - Pipeline analytics
- `GET /api/analytics/performance` - Agent performance
- `GET /api/dashboard` - Full dashboard data
- `POST /api/campaigns` - Create outreach campaign
- `GET /api/meetings` - Upcoming meetings

## Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| Starter | $97/mo | 500 leads, email only |
| Pro | $297/mo | 5,000 leads, all agents, multi-channel |
| Enterprise | $997/mo | Unlimited, custom agents, API access |

## License

Proprietary - Dutchkem Ventures
