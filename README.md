# Quizness Partner

[![CI/CD](https://github.com/mackenziecox/quiznessPartner/actions/workflows/ci.yml/badge.svg)](https://github.com/mackenziecox/quiznessPartner/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mackenziecox/quiznessPartner/branch/main/graph/badge.svg)](https://codecov.io/gh/mackenziecox/quiznessPartner)

An AI-powered quiz generation application that creates quizzes from uploaded documents or text content. Built with FastAPI, React, and OpenAI.

## Features

- Upload documents (PDF, Text) to generate quizzes
- Enter text directly to create quizzes
- AI-powered question generation using OpenAI
- Interactive quiz-taking experience
- Quiz results and performance tracking
- Responsive design for mobile and desktop

## Tech Stack

### Backend

- **FastAPI**: High-performance API framework
- **SQLAlchemy**: ORM for database interactions
- **PostgreSQL**: Database for storing quizzes and results
- **OpenAI API**: For AI-powered quiz generation
- **PyMuPDF**: For PDF text extraction
- **Pytest**: For unit and integration testing

### Frontend

- **React**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching
- **Vitest**: Testing framework
- **Axios**: HTTP client

### DevOps

- **Docker**: Containerization
- **Docker Compose**: Container orchestration
- **GitHub Actions**: CI/CD
- **NGINX**: Web server and reverse proxy

## Setup for Development

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.9+
- OpenAI API Key

### Environment Setup

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/quizness-partner.git
   cd quizness-partner
   ```

2. Create a `.env` file in the root directory

   ```
   OPENAI_API_KEY=your_openai_api_key
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=quizness
   DATABASE_URI=postgresql://postgres:postgres@db:5432/quizness
   BACKEND_CORS_ORIGINS=http://localhost:3000
   ```

3. Start the application with Docker Compose

   ```bash
   docker compose up -d
   ```

4. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API documentation: http://localhost:8000/docs

### Running Tests

#### Backend Tests

```bash
cd backend
python -m pytest tests/
```

#### Frontend Tests

```bash
cd frontend
npm test
```

## Production Deployment

1. Update the production environment variables in `.env.prod`

2. Build and run the production containers

   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

3. Set up SSL certificates with Certbot

   ```bash
   docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d example.com
   ```

4. The application will be available at your domain with HTTPS

## Project Structure

```
quizness-partner/
├── backend/
│   ├── models/           # Database models
│   ├── tests/            # Backend tests
│   ├── ai_utils.py       # OpenAI integration
│   ├── db_utils.py       # Database utilities
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/          # API clients
│   │   ├── components/   # Reusable UI components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Page components
│   │   └── types/        # TypeScript type definitions
│   ├── package.json      # Node.js dependencies
│   └── vite.config.ts    # Vite configuration
├── docker/               # Docker configuration files
├── .github/workflows/    # GitHub Actions CI/CD
├── docker-compose.yml    # Development Docker Compose
└── docker-compose.prod.yml # Production Docker Compose
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT API
- LangChain for AI integration
- All contributors and users of the project
