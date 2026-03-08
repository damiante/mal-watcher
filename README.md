# MAL Watcher

A Python service that automatically synchronizes anime from MyAnimeList user lists to Sonarr, making it easy to track and download anime you're watching or plan to watch.

## Features

- Automatically syncs anime from MyAnimeList to Sonarr
- Supports multiple tracked users
- Filters for TV anime only (skips movies, OVAs, etc.)
- Intelligent title matching to avoid duplicates
- Runs as a daemon with configurable sync intervals
- Docker support for easy deployment
- Manual run mode for testing
- Comprehensive logging with debug mode

## How It Works

1. Periodically checks MyAnimeList for each tracked user
2. Retrieves anime with status: "Watching", "Plan to Watch", or "On Hold"
3. Filters for TV anime only
4. Compares with Sonarr's tracked series to avoid duplicates
5. Automatically adds new anime to Sonarr for tracking and downloading

## Prerequisites

- Python 3.11 or higher
- MyAnimeList API Client ID ([Get one here](https://myanimelist.net/apiconfig))
- Sonarr instance with API access
- Docker (optional, for containerized deployment)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mal-watcher.git
cd mal-watcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create your configuration:
```bash
cp config.yaml.example config.yaml
```

4. Edit `config.yaml` and fill in your settings:
```yaml
env-prod:
  - name: X-MAL-CLIENT-ID
    value: your_mal_client_id_here
  - name: SEARCH_FREQUENCY_MINUTES
    value: 60
  - name: MAL_TRACKED_USERS_FILE
    value: ./tracked_users
  - name: SONARR_URL
    value: http://your-sonarr-url:8989
  - name: SONARR_API_KEY
    value: your_sonarr_api_key_here
  - name: LOG_LEVEL
    value: INFO
```

5. Create a `tracked_users` file with one username per line:
```
username1
username2
```

### Docker Installation

1. Pull the image from GitHub Container Registry:
```bash
docker pull ghcr.io/damiante/mal-watcher:latest
```

2. Create your configuration files (`config.yaml` and `tracked_users`)

3. Run with Docker:
```bash
docker run -d \
  --name mal-watcher \
  -v /path/to/config.yaml:/app/config.yaml:ro \
  -v /path/to/tracked_users:/app/tracked_users:ro \
  ghcr.io/damiante/mal-watcher:latest
```

Or use environment variables:
```bash
docker run -d \
  --name mal-watcher \
  -e X_MAL_CLIENT_ID=your_client_id \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_api_key \
  -e SEARCH_FREQUENCY_MINUTES=60 \
  -e LOG_LEVEL=INFO \
  -v /path/to/tracked_users:/app/tracked_users:ro \
  ghcr.io/damiante/mal-watcher:latest
```

### Docker Compose

Create a `docker-compose.yml`:
```yaml
version: '3.8'

services:
  mal-watcher:
    image: ghcr.io/damiante/mal-watcher:latest
    container_name: mal-watcher
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./tracked_users:/app/tracked_users:ro
    restart: unless-stopped
    environment:
      - LOG_LEVEL=INFO
```

Then run:
```bash
docker-compose up -d
```

## Usage

### Daemon Mode (Default)

Run continuously with automatic syncing:
```bash
python main.py
```

With Docker:
```bash
docker run -v ./config.yaml:/app/config.yaml:ro -v ./tracked_users:/app/tracked_users:ro ghcr.io/damiante/mal-watcher:latest
```

### Manual Mode

Run once and exit (useful for testing):
```bash
python main.py --manual
```

With Docker:
```bash
docker run -v ./config.yaml:/app/config.yaml:ro -v ./tracked_users:/app/tracked_users:ro ghcr.io/damiante/mal-watcher:latest --manual
```

### Command Line Options

- `--manual`: Run once and exit instead of daemon mode
- `--config PATH`: Path to config file (default: `config.yaml`)
- `--environment ENV`: Environment to load (default: `env-prod`)
- `--log-level LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR)

### Examples

Debug mode:
```bash
python main.py --log-level DEBUG
```

Custom config file:
```bash
python main.py --config /path/to/custom-config.yaml
```

One-time sync with verbose output:
```bash
python main.py --manual --log-level DEBUG
```

## Configuration

### Config File Format

```yaml
env-prod:
  - name: X-MAL-CLIENT-ID
    value: your_mal_client_id
  - name: SEARCH_FREQUENCY_MINUTES
    value: 60
  - name: MAL_TRACKED_USERS_FILE
    value: ./tracked_users
  - name: SONARR_URL
    value: http://localhost:8989
  - name: SONARR_API_KEY
    value: your_sonarr_api_key
  - name: LOG_LEVEL
    value: INFO
```

### Environment Variables

All configuration can be set via environment variables (useful for Docker):

- `X_MAL_CLIENT_ID`: MyAnimeList API Client ID
- `SEARCH_FREQUENCY_MINUTES`: Minutes between sync cycles
- `MAL_TRACKED_USERS_FILE`: Path to tracked users file
- `SONARR_URL`: Sonarr server URL
- `SONARR_API_KEY`: Sonarr API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Tracked Users File

Simple text file with one MAL username per line:
```
MoxPeanut
AnotherUser
YetAnotherUser
```

Note: Users must have public anime lists.

## Project Structure

```
mal-watcher/
├── mal_watcher/           # Main application package
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── mal_client.py      # MyAnimeList API client
│   ├── sonarr_client.py   # Sonarr API client
│   ├── sync.py            # Synchronization logic
│   └── utils.py           # Utility functions
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── config.yaml            # Configuration file (not in git)
├── tracked_users          # Tracked users file (not in git)
└── README.md
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with debug logging
python main.py --manual --log-level DEBUG
```

### Building Docker Image

```bash
docker build -t mal-watcher .
```

## Extending the Project

The project is designed to support additional services like Radarr in the future. To add support:

1. Create a new client module (e.g., `radarr_client.py`)
2. Extend the sync logic in `sync.py`
3. Update configuration to support the new service

## Troubleshooting

### No anime being added

- Check that your Sonarr root folders are configured
- Check that quality profiles exist in Sonarr
- Verify your MAL API client ID is valid
- Run with `--log-level DEBUG` to see detailed matching information

### Authentication errors

- Verify your MAL Client ID is correct
- Verify your Sonarr API key is correct
- Ensure Sonarr URL is accessible from where the service runs

### Duplicates being added

- The service uses fuzzy matching with a threshold
- Adjust the similarity threshold in `utils.py` if needed
- Check Sonarr logs to see if titles are being matched correctly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- MyAnimeList for their public API
- Sonarr team for their excellent API documentation
