# MEXC Arbitrage Bot

This project is a Telegram bot that automatically checks for arbitrage opportunities between prices on MEXC and DexScreener. The bot uses MEXC's API to get price data and contract addresses, and DexScreener's API to compare prices.
After checking all coins, the bot restarts the check.

if you want to change % of spread. Change number in this line (NOT -+) 282 266
## Requirements
   Install the required libraries:

    ```
    pip install -r requirements.txt
    ```

## Configuration

Before running the bot, you need to configure a few parameters:

1. Replace `YOUR MEXC API KEY` with your MEXC API key.
2. Replace `YOUR MEXC SECRET KEY` with your MEXC secret key.
3. Set your Telegram bot API key (obtained when registering the bot).
4. Set the admin ID in the `ADMIN_ID` variable.

## Running the Bot
/start

### Start the Arbitrage Checking:
 Start
 Stop - stoped SHOWING spread not check it (if you want to stop a code do it by ide)

 /add_ignore COIN - added coin to ignored

To start the arbitrage checking process:
if you need to add new network //////////////
valid_networks = {
        "Solana(SOL)": "solana",
        "BNB Smart Chain(BEP20)": "bsc",
    }
 #
add network like this
BNB Smart Chain(BEP20) -MEXC API network info
"bsc" - for dex api
mexc api info - swapped into = bsc
valid_networks = { (with added TON)
        "Solana(SOL)": "solana",
        "BNB Smart Chain(BEP20)": "bsc",
        "Toncoin(TON)": "ton",
    }