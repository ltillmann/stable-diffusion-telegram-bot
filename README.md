Software as a Service (SaaS) Generative AI Stable Diffusion Telegram Bot. Telegram Bot to create a text2image image via the stable diffusion Automatic1111 WebUI API endpoint. 

The bot forwards user input from a telegram message to the API backend. When an image is done generating it is send back to the user. The bot also features a simple payment system and SQL database (SQLite3) to document jobs and basic information.

To work, run a local instance of the WebUI (change parameters if needed). In addition, I added a simple Redis Queue to process multiple requests in sequential order (Redis Server Setup needed).
