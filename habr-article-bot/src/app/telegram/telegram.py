from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    CallbackQuery,
    LinkPreviewOptions,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app import httpxHandler
from app.consts import HABR_ARTICLE_PREFIX
from app.settings import settings
from app.telegram import strings, utils


async def setCommands():
    commands = [
        BotCommand(command="start", description="Start"),
        BotCommand(command="help", description="Help"),
        BotCommand(command="last", description="Get latest article"),
        BotCommand(command="rates", description="Article rates"),
        BotCommand(command="rate", description="Rate article"),
        BotCommand(command="remove_rate", description="Remove article rate"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


class ArticleForm(StatesGroup):
    url = State()

class removeForm(StatesGroup):
    url = State()

class RatingForm(StatesGroup):
    url = State()
    rate = State()


dp = Dispatcher(storage=MemoryStorage())
bot = Bot(
    token=settings.botToken,
    default=DefaultBotProperties(parse_mode=None),
)

ratingRouter = Router()
removeRouter = Router()


class get_whitelist_filter():
    def __call__(self, message: Message) -> bool:
        if settings.enableWhitelist:
            return message.chat.id in settings.whitelist
        else:
            return True

whitelist_filter = get_whitelist_filter()


# Start command
@dp.message(Command("start"))
async def commandStart(message: Message) -> None:
    await message.answer(strings.startCommand + str(message.chat.id) + "\nAnd your userID: " + str(message.from_user.id))  # type: ignore

# Help command
@dp.message(whitelist_filter, Command("help"))
async def commandHelp(message: Message) -> None:
    await message.answer(strings.helpCommand)

# Show all user rates
@dp.message(whitelist_filter, Command("rates"))
async def commandRates(message: Message) -> None:
    msgText = "Not yet implemented.."
    await message.answer(msgText)


# Send latest article
@dp.message(whitelist_filter, Command("last"))
async def commandLast(message: Message):
    try:
        articles = await httpxHandler.getArticles(1)
        if articles == []:
            await message.answer(strings.unexpectedError)
        else:
            for (url, content) in articles:
                heading = utils.getHeading(content)
                articleID = utils.getArticleID(url)

                builder = InlineKeyboardBuilder()
                builder.button(text=strings.showArticle, callback_data=f"showArticle_id={articleID}")

                await message.answer(url + "\n" + heading, reply_markup=builder.as_markup())
    except Exception:
        await message.answer(strings.unexpectedError)


# Rate article by user
@ratingRouter.message(Command("rate"), F.chat.id.in_(settings.whitelist))
async def commandRate(message: Message, state: FSMContext):
    await message.answer(strings.askUrl)
    await state.set_state(ArticleForm.url)

@ratingRouter.message(F.text, ArticleForm.url)
async def captureUrl(message: Message, state: FSMContext):
    await state.update_data(url=message.text)
    msgText = strings.askRating
    await httpxHandler.getArticles(1)

    await message.answer(msgText)
    await state.clear()

@ratingRouter.message(F.text, ArticleForm.url)
async def captureRating(message: Message, state: FSMContext):
    await state.update_data(rating=message.text)
    data = await state.get_data()
    username = str(message.from_user.id)  # type: ignore
    url = str(data.get("url", ""))
    rating = int(data.get("rating", 0))
    try:
        await httpxHandler.rateArticle(username, url, rating)
        await message.answer(strings.ratedSuccessfully)
    except Exception:
        await message.answer(strings.unexpectedError)

    await state.clear()


# Send article from user url
@dp.message(whitelist_filter)
async def messageUrl(message: Message):
    if message.text is None:
        await message.answer(strings.unexpectedError)
        return
    if "https://" not in message.text and "http://" not in message.text:
        await message.answer(strings.invalidUrl)
        return

    try:
        url, content = await httpxHandler.getArticleByUrl(message.text)
        heading = utils.getHeading(content)
        articleID = utils.getArticleID(url)

        builder = InlineKeyboardBuilder()
        builder.button(text=strings.showArticle, callback_data=f"showArticle_id={articleID}")

        await message.answer(url + "\n" + heading, reply_markup=builder.as_markup())
    except Exception:
        await message.answer(strings.unexpectedError)


# Handle button showArticle
@dp.callback_query(F.data.startswith("showArticle"))
async def showArticle(callback_query: CallbackQuery):
    if callback_query.data is None or callback_query.message is None:
        logger.error("callback_query content is None")
        await callback_query.answer()
        return

    # TODO: fix this
    linkPreviewOptions = LinkPreviewOptions(is_disabled=True)

    try:
        url = HABR_ARTICLE_PREFIX + callback_query.data.split("=")[1]
        url, content = await httpxHandler.getArticleByUrl(url)
        parts = utils.splitArticle(content)
        for part in parts:
            await callback_query.message.answer(part)
    except Exception as e:
        logger.error(e)
        await callback_query.message.answer(
            strings.unexpectedError,
            link_preview_options=linkPreviewOptions
        )

    await callback_query.answer()


async def startBot():
    await setCommands()
    if settings.enableWhitelist and settings.notifyStartStop:
        try:
            for i in settings.whitelist:
                await bot.send_message(chat_id=i, text=strings.startBot)
        except Exception as e:
            logger.error(e)
    logger.success("Started bot")

async def stopBot():
    if settings.enableWhitelist and settings.notifyStartStop:
        try:
            for i in settings.whitelist:
                await bot.send_message(chat_id=i, text=strings.stopBot)
        except Exception as e:
            logger.error(e)
    logger.success("Stopped bot")


async def start_bot() -> None:
    dp.startup.register(startBot)
    dp.include_router(ratingRouter)
    dp.include_router(removeRouter)
    dp.shutdown.register(stopBot)
    await dp.start_polling(bot)
