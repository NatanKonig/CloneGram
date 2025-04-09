# CloneGram - [README em Português](https://github.com/NatanKonig/CloneGram/blob/main/README-ptbr.md)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/License-Apache_2.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Telegram-API-blue.svg" alt="Telegram API">
</p>
CloneGram is a powerful and efficient tool for cloning messages between Telegram groups, developed with advanced features to avoid detection and bans.

## 📋 Features

* **Complete Cloning** : Transfer messages, media, documents, and media groups between chats
* **Anti-Ban System** : Advanced mechanisms to simulate human behavior and avoid API limitations
* **Flexible Configuration** : Customize rate limits, delays, and activity settings
* **Progress Resumption** : Continue from where you left off in case of interruptions
* **Night Mode** : Reduces activity during specific hours for more natural behavior
* **Weekend Mode** : Adjusts activity during weekends

## 🚀 Installation

### Prerequisites

* Python 3.12 or higher
* Telegram account
* Telegram API credentials (API ID and API Hash)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/clonegram.git
   cd clonegram
   ```
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Set up the environment file:
   ```bash
   cp .env.exemple .env
   # Edit the .env file with your credentials and settings
   ```

## ⚙️ Configuration

Edit the `.env` file with your settings:

```
ACCOUNT_NAME=my_account
PHONE_NUMBER=+1234567890
PASSWORD=your_telegram_password
API_ID=12345
API_HASH=abcdef1234567890abcdef

ORIGIN_GROUP=source_group_id
DESTINY_GROUP=destination_group_id

# Anti-ban settings (all optional with defaults)
MIN_DELAY=3
MAX_DELAY=5
DAILY_LIMIT=1000
HOURLY_LIMIT=100
DAILY_MEDIA_LIMIT=500
MAX_BATCH_SIZE=50
BATCH_COOLDOWN=300
NIGHT_MODE=true
NIGHT_START=0
NIGHT_END=7
NIGHT_MULTIPLIER=2.0
WEEKEND_MODE=false
WEEKEND_MULTIPLIER=1.5
```

### Getting API ID and Hash

1. Visit https://my.telegram.org/auth
2. Log in with your Telegram account
3. Go to "API development tools"
4. Create a new application and copy the API ID and API Hash

### Group IDs

To get a group ID:

* Add [@username_to_id_bot](https://t.me/username_to_id_bot) to your group
* Or use the group by its username (if it has one)

## 🔧 Usage

Run the bot:

```bash
python -m bot.main
```

The bot will start cloning messages from the origin group to the destination group. Progress is automatically saved in the `progress.json` file.

### Configuration Options

| Setting            | Description                                              | Default |
| ------------------ | -------------------------------------------------------- | ------- |
| MIN_DELAY          | Minimum delay between messages (seconds)                 | 3       |
| MAX_DELAY          | Maximum delay between messages (seconds)                 | 5       |
| DAILY_LIMIT        | Maximum number of messages per day                       | 1000    |
| HOURLY_LIMIT       | Maximum number of messages per hour                      | 100     |
| DAILY_MEDIA_LIMIT  | Maximum number of media messages per day                 | 500     |
| MAX_BATCH_SIZE     | Maximum messages to process before taking a longer break | 50      |
| BATCH_COOLDOWN     | Cooldown time after reaching batch size (seconds)        | 300     |
| NIGHT_MODE         | Reduce activity during night hours                       | true    |
| NIGHT_START        | Night mode start hour (24h format)                       | 0       |
| NIGHT_END          | Night mode end hour (24h format)                         | 7       |
| NIGHT_MULTIPLIER   | Multiply delays by this factor during night hours        | 2.0     |
| WEEKEND_MODE       | Reduce activity during weekends                          | false   |
| WEEKEND_MULTIPLIER | Multiply delays by this factor during weekends           | 1.5     |

## 🐳 Docker

The project includes Docker support for easy deployment.

### Building the image

First, build the Docker image for the project:

```bash
# Set environment variables for the build
export DOCKER_USERNAME=your_username
export IMAGE_TAG=latest

# Build the image
docker build -t $DOCKER_USERNAME/clonegram:$IMAGE_TAG .
```

### First run (interactive mode)

The first time you run the bot, you'll need to authorize your Telegram account. This requires running in interactive mode:

```bash
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/progress.json:/app/progress.json \
  -v $(pwd)/activity_counters.json:/app/activity_counters.json \
  $DOCKER_USERNAME/clonegram:$IMAGE_TAG
```

During this first run, you'll receive a verification code on Telegram. Enter this code in the terminal to complete authentication.

### Background execution

After the initial authentication is complete (and the session file has been created), you can run the bot in the background:

```bash
# Run in background
docker-compose up -d

# Or, without docker-compose:
docker run -d \
  --name clonegram \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/progress.json:/app/progress.json \
  -v $(pwd)/activity_counters.json:/app/activity_counters.json \
  $DOCKER_USERNAME/clonegram:$IMAGE_TAG
```

### Check logs

To check the logs of the running container:

```bash
docker-compose logs -f

# Or, without docker-compose:
docker logs -f clonegram
```

## 📝 Important Note

This project is intended for educational and personal use only. Misuse for spamming or violating Telegram's terms of service is strongly discouraged. The author takes no responsibility for the improper use of this tool.

## 🧩 Project Structure

```
clonegram/
│
├── bot/
│   ├── main.py            # Main entry point
│   ├── progress_tracker.py # Progress management
│   ├── rate_limit.py      # Rate limiting
│   ├── safety.py          # Anti-detection mechanisms
│   ├── settings.py        # Settings
│   └── utils.py           # Various utilities
│
├── sessions/              # Stores Telegram sessions
├── .env.exemple           # Example configuration file
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── pyproject.toml         # Project dependencies and metadata
└── README.md              # Documentation
```

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE]() file for details.

## 👏 Acknowledgements

* [Telethon](https://github.com/LonamiWebs/Telethon) for providing the Python API for Telegram

---
