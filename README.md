# Alpha Coy Admin Bot

A centralised database to track Attendance and Statuses, with methods to generate Parade States and Book In/Book Out Strength.

#

# Operating Guide For Future Batches

## Task TeleBot
This file hosts the telegram handlers and enable updates and request to the database. Commands are used to generate Parade State and BIBO Strength while messages with specific headers are used to update statuses.

```python
# telegram api to handle commands and reply to messages
# note: commands are case sensitive so different variations can be included for those with spelling disability
@bot.message_handler(commands=[""])
def foo(message):
    bot.reply_to(message, "Hello World")

# telegram api to handle any message
@bot.message_handler(func=lambda msg:True)
def foo(message):
    bot.reply_to(message, "Hello World")

# telegram api to register a subsequent handler i.e. await another message after replying to the command
@bot.message_handler(commands=[""])
def foo(message):
    sent_msg = bot.reply_to(message, "Please enter a number from 1-10")
    bot.register_next_step_handler(sent_msg, next_handler)

def next_handler(message):
    # message refers to the reply from another user after the bot's prompt
    if message.text == "7":
        bot.reply_to(message, "Jackpot!")
    else:
        bot.reply_to(message, "L Bozo")
```
Inline Keyboards and other form of markups can also be explored in the future.

## Paradestate Func
Self explanatory, this file generates parade state messages in the specific format HQ requires using data from the database only. No updates are done in this file and functions are request only.

## G-Sheet DB Func
Clearly someone didn't have a good naming sense when creating this file. The function names are even more horrendous but they are prehistoric artifacts so let it slide. 
#### Here contains all the backend processing of the bot, and is the connection between the bot, the database, and the google sheet (now the name makes sense). 

### Update Attendance
- Attendance is updated on the database side before the parade state is generated. 
- Data from the google sheet is used to update the database before the parade state is generated. 
- Data updated varies between am and pm as first and last parade has different considerations:
     - Last Parade strength do not include the stay outs
     - on book out days everyone is absent except those on duty. 
- Logic in this function may not cover every single scenario so **If there is a logic error high chance it is because of this function.**

### Update Info
- New Soldier Information (Platoon, Names, Rank etc.), entirely new soldiers, or soldiers who are removed can be updated using this function. 
- A new ID is generated for new soldiers depending on their name, with increments for repeating similar names. 
- **ALL SOLDIER'S PAST RECORDS AND STATUSES WILL BE DELETED WITH THIS FUNCTION**. Do make backups or double check before deleting people using this function. 

### Update Duty
- Duties are updated automatically at the start of each day. 
- They are sourced from the Overall Duties sheet for commanders, and the Trooper Duties sheet for troopers. 
- **It is format dependent so do change the code to follow the format i.e. date formats, rows and columns added/removed etc.** 

### Update Leave
- Leaves are updated 3 days in advance from the Overall Duties sheet. For commanders only.

### Update G-Sheet And DB...
- The main functions to update google sheet and database. 
- Message is unformatted and details are inserted into google sheet if it affects attendance, and inserted into database regardless. 
- Google sheet is used as a reference to update attendance, Database is used as a way to quickly get the duration of a person's status/leave/appointment etc.

### Add Days G-Sheet
- Add more columns to the google sheet automatically. 
- The first tab is the default worksheet to get and update attendance so do change worksheets and archive old worksheets once in awhile to reduce lag.

## Book In Str
This file generates the book in strength. Absentees are generated from functions in this file so if there is any missing absentees (Leave or MC), debug the code in the get_absent() function.

## Utils
This file contains all the utility functions. Functions to unformat messages, detect errors, format and unformat dates

## Config
This file contains the formats of all the Parade State, BIBO Strength messages.

## Task Duty / FP /LP
This files are ran daily and calls the functions to update Duty, Attendance and send Parade State to the chat daily at a fixed timing.
