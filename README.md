# Nuero Proxy
Simple teleram bot that streams data chunks from LLM to chat.

Using `redis` mini-database that stores ids of users that generate something (this is useless for this moment).

Currently supports only Mistral API (more APIs coming soon).

## Building and running
1. Download the project using `git clone https://github.com/LiptonItTea/nueroProxy`
2. Create files `bot_token.csv` and `mistral_token.csv` with telegram bot token and mistral api token respectively.
3. Build the project using `docker compose build`.
4. Run project using `docker compose up`.