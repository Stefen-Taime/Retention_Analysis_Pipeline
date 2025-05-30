# Video Retention Analytics Pipeline

> Real-time video retention analysis powered by Redpanda, ClickHouse, and AI

A comprehensive data pipeline for analyzing video viewer retention patterns using streaming analytics and artificial intelligence. Built with modern data stack for real-time insights and actionable recommendations.

## Architecture

The pipeline consists of several interconnected components:

**Data Producer** → **Redpanda** → **ClickHouse** → **FastAPI** → **Streamlit UI** → **AI Analysis**

### Components

- **Data Producer**: Generates realistic video viewing events
- **Redpanda**: High-performance streaming platform (Kafka-compatible)
- **ClickHouse**: Columnar database for analytics
- **FastAPI**: REST API for data access
- **Streamlit**: Interactive web interface
- **AI Analysis**: OpenAI GPT-4 

## Features

### Real-time Analytics
- Live video retention curves
- Concurrent viewer tracking  
- Dropoff point detection
- Engagement metrics calculation

### AI-Powered Insights
- **OpenAI GPT-4**: Premium analysis with detailed recommendations
- **Demo Mode**: Intelligent analysis without API keys

### Interactive Visualizations
- Plotly-powered retention curves
- Real-time metrics dashboard
- Significant dropoff identification
- Export functionality for reports

### Scalable Infrastructure
- Containerized with Docker Compose
- Horizontal scaling ready
- Production-grade database optimizations
- Health checks and monitoring

## Technology Stack

### Data Pipeline
- **Redpanda**: Streaming platform
- **ClickHouse**: Analytics database
- **Python**: Data processing

### API & Frontend  
- **FastAPI**: REST API backend
- **Streamlit**: Web interface
- **Plotly**: Interactive charts

### AI Integration
- **OpenAI GPT-4**: Advanced analysis
- **Custom prompts**: Video analytics expertise

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **Nginx**: Load balancing (optional)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended
- API keys (optional for demo mode):
  - OpenAI API key (starts with `sk-`)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Retention_Analysis_Pipeline
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the pipeline**
   ```bash
   docker-compose up -d
   ```

4. **Access the interfaces**
   - **Main UI**: http://localhost:8501
   - **API Docs**: http://localhost:8000/docs
   - **Redpanda Console**: http://localhost:8080
   - **ClickHouse UI**: http://localhost:8081

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
API_BASE_URL=http://api-server:8000

# AI API Keys (optional - for demo mode leave empty)
OPENAI_API_KEY=sk-your-openai-key-here
```

## Usage

### Step 1: Start the Data Pipeline

The system automatically begins generating realistic video viewing data:

```bash
docker-compose up -d
```

### Step 2: Access the Analytics Interface

Navigate to http://localhost:8501 to access the Streamlit interface.

### Step 3: Analyze Video Retention

1. **Select a video** from the dropdown
2. **View metrics**: Unique viewers, completion rate, dropoffs
3. **Analyze charts**: Retention curves and percentage trends
4. **Get AI insights**: Click "Analyze with AI" for recommendations

### Step 4: Export Reports

Generate and download comprehensive analysis reports in Markdown format.

## API Endpoints

### Videos
- `GET /videos` - List all available videos
- `GET /video/{video_id}/retention_curve` - Get retention data
- `GET /video/{video_id}/significant_dropoffs` - Get dropoff points
- `GET /video/{video_id}/engagement_summary` - Get engagement metrics

### Health
- `GET /health` - API health check
- `GET /` - API status

## Configuration

### Data Producer Settings

The producer generates realistic viewing patterns:

- **Multiple user behaviors**: casual, binge, skipper, completer
- **Realistic dropoff probabilities**: Higher at beginning and end
- **Session variety**: 30 seconds to 30 minutes
- **Concurrent users**: 1-8 simultaneous sessions

### ClickHouse Optimization

Optimized for analytics workloads:

- **Partitioning**: By month for efficient queries
- **Compression**: Optimized storage
- **Materialized views**: Real-time aggregations
- **Memory settings**: Configured for analytics

### AI Analysis Prompts

Sophisticated prompts for actionable insights:

- **Retention assessment**: Good/average/poor evaluation
- **Critical moment identification**: Dropoff analysis
- **Hypothesis generation**: Content-based suggestions
- **Actionable recommendations**: Specific improvements

## Development

### Project Structure

```
Retention_Analysis_Pipeline/
├── api/                    # FastAPI backend
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── clickhouse_init/        # Database initialization
│   └── init.sql
├── llm-interface/          # Streamlit frontend
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── producer/               # Data generator
│   ├── Dockerfile
│   ├── producer.py
│   └── requirements.txt
├── docker-compose.yml      # Service orchestration
├── .env                    # Environment variables
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

### Adding New Features

1. **Backend (FastAPI)**
   - Add endpoints in `api/main.py`
   - Update data models as needed
   - Test with `/docs` interface

2. **Frontend (Streamlit)**
   - Modify `llm-interface/app.py`
   - Add new visualizations
   - Extend AI analysis prompts

3. **Database (ClickHouse)**
   - Update `clickhouse_init/init.sql`
   - Add new materialized views
   - Optimize queries for performance

### Local Development

```bash
# Start individual services for development
docker-compose up redpanda clickhouse-server
docker-compose up api-server
docker-compose up llm-interface
```

## Monitoring

### Health Checks

All services include health checks:
- **API**: HTTP endpoint checks
- **ClickHouse**: Query execution
- **Redpanda**: Cluster status
- **Producer**: Process monitoring

### Logging

View logs for debugging:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f llm-interface
docker-compose logs -f api-server
docker-compose logs -f data-producer
```

### Metrics

Monitor performance:
- **ClickHouse**: Query performance, storage usage
- **Redpanda**: Message throughput, lag
- **API**: Response times, error rates

## Troubleshooting

### Common Issues

#### API Connection Errors
```bash
# Check API health
curl http://localhost:8000/health

# Restart API service
docker-compose restart api-server
```

#### ClickHouse Connection Issues
```bash
# Test ClickHouse connectivity
docker exec -it clickhouse-server clickhouse-client --query "SELECT 1"

# Check initialization logs
docker-compose logs clickhouse-server
```

#### AI Analysis Not Working
1. Verify API keys in `.env` file
2. Check API key formats:
   - OpenAI: starts with `sk-`
3. Restart interface: `docker-compose restart llm-interface`

#### No Data in Interface
1. Check producer is running: `docker-compose logs data-producer`
2. Verify Redpanda connectivity: http://localhost:8080
3. Check ClickHouse data: Access UI at http://localhost:8081

### Performance Tuning

#### For High Volume
- Increase ClickHouse memory settings
- Add more Redpanda partitions  
- Scale producer instances
- Optimize database queries

#### For Low Resources
- Reduce producer event rate
- Decrease retention thresholds
- Limit concurrent sessions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style

- **Python**: Follow PEP 8
- **SQL**: Use consistent formatting
- **Docker**: Multi-stage builds preferred
- **Documentation**: Update README for new features

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Redpanda**: High-performance streaming platform
- **ClickHouse**: Powerful analytics database
- **OpenAI**: Advanced language models
- **Streamlit**: Excellent Python web framework

## Support

For questions, issues, or contributions:

1. **Issues**: Use GitHub Issues for bugs and feature requests
2. **Discussions**: Use GitHub Discussions for general questions


---

**Built with ❤️**