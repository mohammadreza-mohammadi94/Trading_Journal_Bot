from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.bot_management import is_valid_date, is_valid_time, return_to_main_menu
from utils.states_manager import TradeStates
from database.database_management import TradeDatabase


# Create a instance of TradeDatabase.
trades_db = TradeDatabase()


async def new_trade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the process of adding a new trade by asking the user to select a ticker.
    
    Args:
        update (Update): The update object that contains the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (WIN_LOSS).
    """
    query = update.callback_query
    await query.answer()
    tickers = trades_db.get_all_tickers()

    keyboard = [[InlineKeyboardButton(ticker, callback_data=ticker)] for ticker in tickers]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Please Choose Ticker's Name.", reply_markup=reply_markup)
    return TradeStates.WIN_LOSS


async def win_loss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the selection of the trade result (Win/Loss) and prompts the user to choose the side (Long/Short).
    
    Args:
        update (Update): The update object that contains the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (SIDE).
    """
    query = update.callback_query
    await query.answer()
    
    context.user_data['ticker_name'] = query.data  # Store selected ticker
    
    keyboard = [
        [InlineKeyboardButton("Win", callback_data='Win')],
        [InlineKeyboardButton("Loss", callback_data='Loss')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Trade Status? (WIN/LOSS).", reply_markup=reply_markup)
    return TradeStates.SIDE


async def side_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the selection of the trade side (Long/Short) and prompts the user to select a trading strategy.
    
    Args:
        update (Update): The update object that contains the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (STRATEGY).
    """
    query = update.callback_query
    await query.answer()
    
    context.user_data['win_loss'] = query.data  # Store win/loss status
    
    keyboard = [
        [InlineKeyboardButton("Long", callback_data='Long')],
        [InlineKeyboardButton("Short", callback_data='Short')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text= "Position Side? (Buy/Sell)", reply_markup=reply_markup)
    return TradeStates.STRATEGY


async def strategy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the selection of the trading strategy and prompts the user to enter the trade date.
    
    Args:
        update (Update): The update object that contains the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (DATE).

    Currently, available strategies are:
    - MTR
    - FF
    - Close NYSE
    - DHL (High/Low previous day) 
    """
    query = update.callback_query
    await query.answer()
    
    context.user_data['side'] = query.data # store trade's side
    
    keyboard = [
        [InlineKeyboardButton("DHL", callback_data='DHL')],
        [InlineKeyboardButton("Close NYSE", callback_data='Close_NYSE')],
        [InlineKeyboardButton("MTR", callback_data='MTR')],
        [InlineKeyboardButton("FF", callback_data="FF")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text= "Trading Setup?", reply_markup=reply_markup)
    return TradeStates.RR


async def rr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Asks the user to enter the Risk:Reward ratio of the trade.
    
    Args:
        update (Update): The update object that contains the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (PNL).
    """
    
    query = update.callback_query
    await query.answer()

    # Collect Date
    context.user_data['strategy'] = query.data     # Store trade time
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text="What is Risk:Reward Ratio?"
    )
    return TradeStates.PNL


async def pnl_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """
    Asks the user to enter the Profit and Loss (PnL) of the trade.
    
    Args:
        update (Update): The update object that contains the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (PHOTO).
    """
    context.user_data['rr'] = update.message.text       # Store Risk:Reward ratio
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text="What was PnL?"
    )
    return TradeStates.DATE


async def date_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """
    Asks the user to enter the date of the trade.
    
    Args:
        update (Update): The update object that contains the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (TIME).
    """
    context.user_data['pnl'] = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter the date of the trade (YYYY-MM-DD):"
    )
    return TradeStates.TIME


async def time_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """
    Asks the user to enter the time of the trade.

    Args:
        update (Update): The update object that contains the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.

    Returns:
        int: The next state in the conversation (RR).
    """
    date_str = update.message.text

    if is_valid_date(date_str):
        context.user_data['date'] = update.message.text  # Store the trade date
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="What time was the trade? (HH:MM)"
            )
        return TradeStates.PHOTO
    else:
        await context.bot.send_message("Invalid date format. Please enter the date in YYYY-MM-DD format.")
        return TradeStates.DATE  # Re-ask for the date if it's incorrect


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Asks the user to send a picture of the trade.
    
    Args:
        update (Update): The update object that contains the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: The next state in the conversation (SAVE).
    """
    time_str = update.message.text    # Store PnL

    if is_valid_time(time_str):
        context.user_data['time'] = update.message.text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text="Please Send a Picture of Your Trade."
        )
        return TradeStates.SAVE
    else:
        await context.bot.send_message("Invalid Time format. Please enter the date in HH:MM format.")
        return TradeStates.TIME


async def save_trade_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """
    Saves the trade details to the database.
    
    Args:
        update (Update): The update object that contains the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
    
    Returns:
        int: Ends the conversation.
    """
    context.user_data['photo'] = update.message.photo[-1].file_id   # Store photo 


    # Save the trade details to the database
    trade_id = trades_db.save_trade(
        date= context.user_data['date'], 
        time= context.user_data['time'], 
        ticker = context.user_data['ticker_name'],
        win_loss= context.user_data['win_loss'], 
        side= context.user_data['side'], 
        rr= context.user_data['rr'], 
        pnl= context.user_data['pnl'],
        strategy= context.user_data['strategy'], 
        picture= context.user_data['photo'])

    # Notify user that trade recorded successfully.
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=f"Trade recorded successfully. The Trade ID is {trade_id}."
    )
    # return ConversationHandler.END
    return await return_to_main_menu(update, context)