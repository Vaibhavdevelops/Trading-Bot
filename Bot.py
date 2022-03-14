import discord
from discord.ext import commands

import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt

import io, os

DISCORD_TOKEN = os.environ.get(
    "ODg2MTEwMjQ1ODAwMjUxNDEy.YTw0eQ.3kVgEye02-64w-jbYlofTO9Jww8")
ALPACA_KEY_ID = os.environ.get("PKZZMWALM8QQLSTM697V")
ALPACA_KEY_SECRET = os.environ.get("ibrxDAGgAjlLOMykIyT1UW77t9WHWrYpBFu5wLfb")
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'

plt.rcParams.update({
    'xtick.labelsize' : 'small',
    'ytick.labelsize' : 'small',
    'figure.figsize' : [16,9]})

alpaca_api = tradeapi.REST('PKZZMWALM8QQLSTM697V',
                           'ibrxDAGgAjlLOMykIyT1UW77t9WHWrYpBFu5wLfb',
                           base_url= ALPACA_BASE_URL,
                           api_version = 'v2')


bot = commands.Bot(command_prefix = '/')

@bot.command()
async def hello(context):
    await context.send("Hello, Dispaca!")

@bot.command()
async def account(context):
    await context.send("Fetching details!")
    account_info = alpaca_api.get_account()
    account_embed = generate_account_embed(account_info)
    await context.send(embed = account_embed)

@bot.command()
async def last_price(context, ticker):
    if isinstance(ticker, str):
        ticker = ticker.upper()
    
    await context.send(f"Fetching Last Price for {ticker}")
    try:
        last_price = alpaca_api.get_last_trade(ticker)
        await context.send(f"{ticker} -- ${last_price.price}")
    
    except Exception as e:
        await context.send(f"Error!! Please Check you spelled it correctly. {e}")

@bot.command()
async def check(context, ticker):
    await context.send(f"Wait, while we are plotting Graph!")
    if isinstance(ticker, str):
        ticker = ticker.upper()

    try:
        bars = alpaca_api.get_barset(ticker, 'day', limit = 100)
        bars = bars.df[ticker]
        
        fig = io.BytesIO()
        last_price = bars.tail(1)['close'].values[0]

        plt.title(f"{ticker} -- Last Price ${last_price: .02f}")
        plt.xlabel("Last 100 Days")
        plt.plot(bars["Close"])

        plt.savefig(fig, format="png")
        fig.seek(0)

        await context.send(file= discord.File(fig, f"{ticker}.png"))

        plt.close()

    except Exception as e:
        await context.send(f"Oops, Error!! {e}")


def generate_account_embed(account):
    embed = discord.Embed(title="Account Info", description="Trading Options", color=0x12e8f8)


    embed.add_field(name="Available Cash to Buy", value="$1", inline=False)
    embed.add_field(name="Total Cash", value="$1", inline=False)
    embed.add_field(name="Equity Amount", value="$1", inline=False)
    return embed

def generate_buy_embed(ticker, quantity, market_price):
    embed = discord.Embed()
    total_cost = int(quantity)*market_price
    embed = discord.Embed(title = f"Buying {ticker}",
    description = "Review your buy order below.\
        React with 👍 in 30 Seconds to Confirm your Buy")
    embed.add_field(name = "Quantity",
        value=f"{quantity}", inline=False)
    embed.add_field(name="Current Share Cost",
                    value=f"{market_price}", inline=False)
    embed.add_field(name="Estimated Cost",
                    value=f"{total_cost}", inline=False)
    embed.add_field(name="In Force",
                    value="Good Until Cancelled", inline=False)


@bot.command()
async def buy(context, ticker, quantity):
    if isinstance(ticker, str):
        ticker = ticker.upper()
    try:
        last_trade = alpaca_api.get_last_trade(ticker)
        last_price = last_trade.price
    except Exception as e:
        await context.send(f"Oops! Error getting the last Price: {e}")
        return
    buy_embed = generate_buy_embed(ticker, quantity, last_price)

    await context.send(embed = buy_embed)

    def check(reaction, user):
        return user == context.message.author
    
    try:
        reaction, user = await bot.wait_for("reaction_add",
        timeout=30.0, check=check)
    
    except TimeoutError:
        await context.send("Cancelling the Trade. No Activity Please!")

    else:
        if str(reaction.emoji) == '👍':
            await context.send("Execcuting Your Trade")
            placed_order = alpaca_api.submit_order(symbol = ticker,
            qty= quantity, side='buy', type= 'market', time_in_force='GTC')
            await context.send(f"Order ID: {placed_order.id}")
        
        else:
            await context.send("Cancelling Order!")

bot.run('ODg2MTEwMjQ1ODAwMjUxNDEy.YTw0eQ.3kVgEye02-64w-jbYlofTO9Jww8')