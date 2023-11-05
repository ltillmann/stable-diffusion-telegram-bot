from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


keyboard1 = [[InlineKeyboardButton("🔞 Undress Image 🔞", callback_data='1')],
            [InlineKeyboardButton("Show my 🆔", callback_data='2'),
	     InlineKeyboardButton("🔑 Buy Tokens", callback_data='4')],
	    [InlineKeyboardButton(text="Support", url="https://t.me/undresser_theone_support_bot")]]

keyboard2 = [[InlineKeyboardButton("⬅️ Back", callback_data='3')]]

keyboard3 = [[InlineKeyboardButton("⬅️ Back", callback_data='3'),
	      InlineKeyboardButton("🔑 Buy Tokens", callback_data='4')]]

keyboard4 = [[InlineKeyboardButton("1 🔑", callback_data='6'),
             InlineKeyboardButton("2 🔑", callback_data='7'),
	     InlineKeyboardButton("5 🔑", callback_data='8'),
	     InlineKeyboardButton("10 🔑", callback_data='9')],
	    #[InlineKeyboardButton("20 🔑", callback_data='10'),
             #InlineKeyboardButton("50 🔑", callback_data='11'),
	     #InlineKeyboardButton("100 🔑", callback_data='12'),
	     #InlineKeyboardButton("200 🔑", callback_data='13')],
	    #[InlineKeyboardButton("500 🔑", callback_data='19'),
             #InlineKeyboardButton("1000 🔑", callback_data='20')],
	    [InlineKeyboardButton("⬅️ Back", callback_data='3')]]


keyboard5 = [[InlineKeyboardButton("Crypto Bot 💎", callback_data='14'),
              InlineKeyboardButton("💳 Card", callback_data='15')],
	     [InlineKeyboardButton("⬅️ Back ", callback_data='3')]]


keyboard6 = [[InlineKeyboardButton("🔞 Undress Image 🔞", callback_data='16')],
            [InlineKeyboardButton("Show my 🆔", callback_data='2'),
	     InlineKeyboardButton("🔑 Buy Tokens", callback_data='16')],
	    [InlineKeyboardButton(text="Support", url="https://t.me/undresser_theone_support_bot")]]


keyboard7 = [[InlineKeyboardButton("I Agree ✅", callback_data='18'),
	   InlineKeyboardButton("Decline ❌", callback_data='17')]]

keyboard8 = [[InlineKeyboardButton("USDT", callback_data='USDT'), 
InlineKeyboardButton("TON", callback_data='TON'),
InlineKeyboardButton("BTC", callback_data='BTC'),
InlineKeyboardButton("ETH", callback_data='ETH')],
[InlineKeyboardButton("LTC", callback_data='LTC'),
InlineKeyboardButton("BNB", callback_data='BNB'),
InlineKeyboardButton("TRX", callback_data='TRX'),
InlineKeyboardButton("USDC", callback_data='USDC')],
[InlineKeyboardButton("⬅️ Back ", callback_data='3')]]


reply_markup_button = InlineKeyboardMarkup(keyboard1)
reply_markup_menu = InlineKeyboardMarkup(keyboard2)
reply_markup_tokens_menu = InlineKeyboardMarkup(keyboard3)
reply_markup_buyoptions = InlineKeyboardMarkup(keyboard4)
reply_markup_payment_methods = InlineKeyboardMarkup(keyboard5)
reply_markup_start = InlineKeyboardMarkup(keyboard6)
reply_markup_agreement = InlineKeyboardMarkup(keyboard7)
reply_markup_cryptoassets = InlineKeyboardMarkup(keyboard8)

################################################################


keyboard_support_faq = [["How to buy tokens?"], 
["How to pay with Crypto Bot?"], 
["How to undress an image?"], 
["Why is the bot not working?"], 
["I have another question"]]

reply_markup_faq = ReplyKeyboardMarkup(keyboard_support_faq)
