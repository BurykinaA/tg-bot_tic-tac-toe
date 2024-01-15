"""
Bot for playing tic tac toe game with multiple CallbackQueryHandlers.
"""
import logging
import os
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from base_game import (
    CROSS,
    ZERO,
    Game,
    Move,
    Symbol,
    Field,
    get_default_state,
    next_move,
    check_winner,
)



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TOKEN = os.getenv('TG_TOKEN', "value does not exist")
# print(TOKEN)

(WAITING_FOR_GAME_TYPE,
 WAITING_FOR_SYMBOL,
 CONTINUE_GAME, 
 CONTINUE_GAME_SINGLEPLAYER,
 WAITING_FOR_NEW_GAME) = range(5)


def generate_keyboard(state: list[list[str]]) -> list[list[InlineKeyboardButton]]:
    """Generate tic tac toe keyboard 3x3 (telegram buttons)"""
    return [
        [
            InlineKeyboardButton(state[r][c], callback_data=f'{r}{c}')
            for r in range(3)
        ]
        for c in range(3)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Добавляем выбор типа игры (синглплейер или мультиплейер)
    keyboard = [
        [InlineKeyboardButton("Singleplayer", callback_data="singleplayer")],
        [InlineKeyboardButton("Multiplayer", callback_data="multiplayer")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the game type:", reply_markup=reply_markup)
    
    return WAITING_FOR_GAME_TYPE


async def choose_game_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's choice of the game type."""
    query = update.callback_query
    game_type = query.data
    
    if game_type == "singleplayer":
        context.user_data["active_singleplayer_game"] = True
        # Если выбран синглплейер, предоставляем выбор между X, O и случайным выбором
        keyboard = [
            [InlineKeyboardButton("X", callback_data="X")],
            [InlineKeyboardButton("O", callback_data="O")],
            [InlineKeyboardButton("Random", callback_data="random")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose your symbol:", reply_markup=reply_markup)
        return WAITING_FOR_SYMBOL

    elif game_type == "multiplayer":
        # context.user_data['keyboard_state'] = get_default_state()
        # keyboard = generate_keyboard(context.user_data['keyboard_state'])
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # await query.edit_message_text("X (your) turn! Please, put X to the free place", reply_markup=reply_markup)
        return CONTINUE_GAME




async def mark_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process mark choice from user in singleplayer game and show InlineKeyboard"""
    query = update.callback_query
    await query.answer()

    mark_choice = query.data
    if mark_choice == "X":
        mark = CROSS
    elif mark_choice == "O":
        mark = ZERO
    elif mark_choice == "random":
        mark = random.choice([CROSS, ZERO])

    keyboard = generate_keyboard(get_default_state())
    reply_markup = InlineKeyboardMarkup(keyboard)

    new_game = Game()
    context.user_data["Game"] = new_game
    handle = new_game.get_handle(mark)
    context.user_data["handle_player"] = handle
    context.user_data["handle_bot"] = new_game.get_handle(what_is_left=True)

    my_mark = handle.symbol
    if context.user_data["handle_player"].is_my_turn():
        text = rf"*It is your turn*\. Your mark: {my_mark}\."
    else:
        text = "Waiting for a bot to make a move"

    await query.edit_message_text(
        text=text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )
    if not handle.is_my_turn():
        await bot_turn(update, context)

    logger_message = (
        f"singleplayer game {context.user_data['Game']} has begun, keyboard rendered"
    )
    logger.info(logger_message)
    return CONTINUE_GAME_SINGLEPLAYER


async def game_singleplayer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main processing of the game"""
    query = update.callback_query
    coords_keyboard = query.data

    move = Move([int(coords_keyboard[0]), int(coords_keyboard[1])])
    handle = context.user_data["handle_player"]

    print(move)
    handle(move)
    # try:
    #     handle(move)
    # except:
    #     await query.answer(text=f"Illegal move", show_alert=True)
    #     return CONTINUE_GAME_SINGLEPLAYER

    gc: Game = context.user_data["Game"]
    keyboard = generate_keyboard(gc.grid)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        reply_markup=reply_markup, text="Opponent's turn"
    )
    # logger.info(f"Player made move {move}, message rendered")
    await query.answer()

    if gc.is_game_over:
        del context.user_data["active_singleplayer_game"]
        return await end_singleplayer(update, context)
    return await bot_turn(update, context)


async def bot_turn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bot makes a move in a singleplayer game."""
    query = update.callback_query
    gc = context.user_data["Game"]
    grid = gc.grid
    handle = context.user_data["handle_bot"]
    move = next_move(grid, handle.symbol)
    print('bot', move)
    handle(move)

    keyboard = generate_keyboard(gc.grid)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        reply_markup=reply_markup,
        text="*Your turn*",
        parse_mode="MarkdownV2",
    )
    # logger.info(f"bot made move {move}, message rendered")
    gc: Game = context.user_data["Game"]
    if gc.is_game_over:
        del context.user_data["active_singleplayer_game"]
        return await end_singleplayer(update, context)
    return CONTINUE_GAME_SINGLEPLAYER


async def start_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text.lower()

    if user_choice == "yes":
        # Ваш код для начала новой игры
        await update.message.reply_text("Starting a new game...")
        return WAITING_FOR_GAME_TYPE

    await update.message.reply_text("Okay, no new game for now.")

    return ConversationHandler.END


async def end_singleplayer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """

    game_name = context.user_data["Game"]
    # logger.info(f"{game_name} has ended")
    query = update.callback_query

    gc: Game = context.user_data["Game"]
    handle = context.user_data["handle_player"]
    winner = check_winner(gc.grid)
    
    await query.answer()

    keyboard = [
        ["Yes", "No"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await query.message.reply_text(
        f"The game has ended. Winner: {winner}, That means \nDo you want to start a new game?",
        reply_markup=reply_markup
    )

    return WAITING_FOR_NEW_GAME
    # del context.user_data["bot_message"] 

    # logger_message = (
    #     f"singleplayer game {game_name} has ended, message rendered. winner: {winner}"
    # )
    # logger.info(logger_message)

    # return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    

    # block is False so we don't get blocked while sending a message
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],
        states={
            WAITING_FOR_GAME_TYPE: [
                CallbackQueryHandler(
                    choose_game_type, pattern="^singleplayer$|^multiplayer$", block=False
                ),
            ],
            WAITING_FOR_SYMBOL: [
                CallbackQueryHandler(
                    mark_choice, pattern="^X$|^O$|^random$", block=False
                ),
            ],
            CONTINUE_GAME_SINGLEPLAYER: [
                CallbackQueryHandler(
                    game_singleplayer, pattern="^[0-2][0-2]$", block=False
                ),
            ],
            WAITING_FOR_NEW_GAME: [
                CallbackQueryHandler(
                    start_new_game, pattern="^^(Yes|No)$", block=False
                ),
            ]

        },
        fallbacks=[
            CommandHandler("start", start, block=False),
        ],
        per_message=False,
        block=False,
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()