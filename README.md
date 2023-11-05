Software as a Service (SaaS) Generative AI Stable Diffusion Telegram Bot.
Telegram Bot to create a text2image image via the stable diffusion Automatic1111 WebUI API. The Bot takes user input from telegram and forwards it to the API backend. When an image is done generating it is send back to the user. The bot also employs a simple payment system and SQL database (SQLite3) to document jobs.

To work, run a local instance of the WebUI (change default port if needed). In addition, I added a simple Redis Queue to process multiple requests in sequential order (Redis Server needed).
