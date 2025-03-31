# Cryptocurrency Prediction API

A Flask-based API service that provides cryptocurrency price predictions using machine learning models hosted on Hugging Face, real-time data from Binance, and market sentiment analysis.

## Features

- **Real-time Price Monitoring**: WebSocket integration with Binance for live cryptocurrency price data
- **Machine Learning Predictions**: API integration with Hugging Face for price predictions
- **Market Sentiment Analysis**: Tracks and stores Fear & Greed Index data
- **WebSocket Updates**: Real-time updates to connected clients
- **Database Integration**: Stores historical data and predictions in PostgreSQL

## Live API

The API is deployed and available at:
https://coin-predictor-api-production.up.railway.app

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL database

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/coin-predictor-api.git
cd coin-predictor-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with the following variables
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/coin_predictor
HUGGINGFACE_API_URL=https://your-huggingface-endpoint.com/predict
```

5. Initialize the database:
```bash
flask db upgrade
```

## Usage

### Starting the API Server

```bash
flask run
```

Or for production:

```bash
gunicorn app:app
```

### Components

- **Binance Manager**: Handles data retrieval from Binance API and maintains WebSocket connections for real-time updates
- **Prediction Manager**: Processes data and sends it to the Hugging Face model for predictions
- **Fear & Greed Manager**: Retrieves and stores market sentiment data from Alternative.me API

## API Endpoints

- `GET /api/predictions`: Get latest price predictions
- `GET /api/klines`: Get historical price data
- `GET /api/fear-greed`: Get fear and greed index data

## WebSocket Events

- `kline_update`: Real-time price updates from Binance

## Architecture

The application follows a modular architecture with separate managers for different components:

1. **Data Collection**: Binance Manager retrieves historical and real-time price data
2. **Prediction**: Prediction Manager sends data to Hugging Face ML models and stores results
3. **Sentiment Analysis**: Fear & Greed Manager tracks market sentiment
4. **API Layer**: Flask endpoints expose data to clients
5. **Real-time Updates**: SocketIO enables push updates to clients

## Dependencies

The project uses several key libraries:
- Flask: Web framework
- Flask-SocketIO: WebSocket support
- SQLAlchemy: Database ORM
- Pandas: Data manipulation
- Requests: HTTP requests
- WebSocket-client: WebSocket connections

## Deployment

The application is currently deployed on Railway. You can access the production API at:
```
https://coin-predictor-api-production.up.railway.app
```

To deploy your own instance on Railway:
1. Fork this repository
2. Connect Railway to your GitHub account
3. Create a new project from the repository
4. Add the necessary environment variables
5. Deploy the application

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[MIT](LICENSE)
