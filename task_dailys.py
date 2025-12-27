from telegrambot import bot, CHAT_ID
import random
import os
from config import SERVICE_ACCOUNT, sheet_url
import utils

gc = SERVICE_ACCOUNT
sh = gc.open_by_url(sheet_url)
worksheet = sh.get_worksheet(0)

now = utils.get_now()
current_hour = now.hour
A1col, col = utils.get_today_col(worksheet,now)
today_activity = worksheet.col_values(col)[2]

reminder_hours = [10, 14, 17]
if "MOVEMENT" in today_activity and current_hour in reminder_hours:
    chat_id = CHAT_ID["ALPHA BOT UPDATES"]["CHAT_ID"]
    message_thread_id = CHAT_ID["ALPHA BOT UPDATES"]["THREAD_ID"]

    reminder = "Remember to do daily 30s"
    sm_unglam = ['CAACAgUAAxkBAAEwZr1ncSMmkzZsGB0s09YqCj3uRFHtrQACNBQAArxUiFdzm4eUYcnDVDYE', 'CAACAgUAAxkBAAEwZr9ncSNOgvLs84aZZaSfCcs6JyhAbQACTRIAAlr5kVcyE3bgY0kFxDYE', 'CAACAgUAAxkBAAEwZsFncSNQiQgqokFc45KpeIr--XLmDQACUxMAAmB1iFfV7X34m1BUwzYE', 'CAACAgUAAxkBAAEwZsNncSNSg98EXQXqZygxtqoxXeHU6AACBxQAAmuTiFfVNQ8vj4WlkTYE', 'CAACAgUAAxkBAAEwZsVncSNTDDk0aKM1vK2q1dJ90wLVawACsxYAAjHJiVc6_-YEQXTTJjYE', 'CAACAgUAAxkBAAEwZsdncSNVI1KYlrsd79N1P-oQXRyfQAACRREAAi0_iFeRwT-J-PYIlDYE', 'CAACAgUAAxkBAAEwZslncSNW0gxx75je3shovlS71pgRSAAC6BUAAmAliFcewHjAnHHpsDYE', 'CAACAgUAAxkBAAEwZstncSNYIE3ns-m08UYqUiDwPn10DgAC8xMAApXHiFd5QztxZhbvAjYE', 'CAACAgUAAxkBAAEwZs1ncSNZ2qtJOjsSvT90O9nA6gjQVQACchQAAnhXiFcIYTf2Ni_rKjYE', 'CAACAgUAAxkBAAEwZs9ncSNcGeJLLflXenCU0S9ji4pceQACjRUAAmcciFemIHmFrWvwETYE', 'CAACAgUAAxkBAAEwZtBncSNdLhxEK7Xiv73cfhNwQcAzJgACWhUAAp8SiVc46DGOk3rs_TYE', 'CAACAgUAAxkBAAEwZtJncSNeyJPCb2fS2ICgtVI26NRRWAACeQ8AAnpIkVeeupYoLrwxpTYE', 'CAACAgUAAxkBAAEwZtNncSNe_okbcENUVvbjMgy-jgABWw4AAqYSAAKCs4hX6NzS_dX0dxA2BA', 'CAACAgUAAxkBAAEwZtVncSNemupCmBAfrVBIFhJLxy0b7AAC2RIAAs8AAYlXATQRrWqph3M2BA', 'CAACAgUAAxkBAAEwZtdncSNfVKDWGKiKbAABWjgpOJfOHbEAAnMSAAIOrYhXsOwuA-UaS8o2BA', 'CAACAgUAAxkBAAEwZtlncSNfaw77SwQNjCRoVreZvwAB7b8AArwSAAKxMJBXHUc7ShBqha42BA', 'CAACAgUAAxkBAAEwZttncSNfWK-igkr2bkGPN7Uoblwz2AACERUAAhwPiFc5rmluvEs4TTYE', 'CAACAgUAAxkBAAEwZt1ncSNgNUK6UexhZg2DuQzK5DeaSwACPRUAAjpFiFfnOayCkCZw6zYE', 'CAACAgUAAxkBAAEwZuBncSNgHjCW7jt0Zs6EBEAnaWkYtQACHhgAAjDriFcMSAsrmQnAtjYE', 'CAACAgUAAxkBAAEwZuJncSNh6nJHEsrD5vjtcPwSEwdKkQAC1hQAAptVkVcvCkWVRUqR5jYE', 'CAACAgUAAxkBAAEwZuNncSNhNPbehlwMeyqWFcfAJglkIwACzRMAAhXkiFd3zMLrx8-C5TYE', 'CAACAgUAAxkBAAEwZuVncSNhbKQTrJ3-82KRcgd9EfKntwACyRMAAk1ciVftJcYXfer5wDYE', 'CAACAgUAAxkBAAEwZudncSNi6-Ch-BXrwFiCeY7ztaW_2gACGBMAAiwHiVfEvHUKUnm19jYE', 'CAACAgUAAxkBAAEwZulncSNitqlxiyR7CXXVOw2lXx7cBQACyBIAApUviFcFOxOLFvUPnTYE', 'CAACAgUAAxkBAAEwZuxncSNjH83xQFEm4JL4In0ZOu3jYgACxhQAAp9GiFc3J_GOw28mSzYE', 'CAACAgUAAxkBAAEwZu1ncSNjzj-ddgETP69lwrPfUD8k3AACIhYAAkRYiFf3fJIr7Czi8jYE', 'CAACAgUAAxkBAAEwZu9ncSNj2fXPCIETM6uKWiFhzHIl1QAChRQAAq8JiFdigDrTNtAIRzYE', 'CAACAgUAAxkBAAEwZvJncSNkR87D5cBAYhX05UPKvaRj8wACLxMAAutAiVeDTAa3WVM6BzYE', 'CAACAgUAAxkBAAEwZvRncSNkP8dHSoW53V3UKlXCpgH5pQACehYAAlP3iFd7YD1CDhBK5DYE', 'CAACAgUAAxkBAAEwZvVncSNkpwEBaBYmmUMORq4Roi7e_gAC1BUAAggMiVcaSDYkSDF1RDYE', 'CAACAgUAAxkBAAEwZvhncSNlQm15vPNVWOffaKYma9FotgAC8RUAAnW0iFdTajbaV-RpyDYE', 'CAACAgUAAxkBAAEwZvZncSNlBwX0P6fiYsuQ0E-Xm2DRPAACdxcAArDziFfVgR9sR1PntTYE',"CAACAgUAAxkBAAEwZy1ncS6qW9zRmCjYXIciXSOVrreyQwACUA8AAvwC-VZQkn_4mWFiwjYE","CAACAgUAAxkBAAEwZzFncS6_Omp8dZhWP6GDeNau3JFN2QACLBAAAmAS-FYtntHU_uSHfTYE","CAACAgUAAxkBAAEwZzNncS7Kj2MDr_V2cZZv3QlGa9EraQACTRMAAmNZ2FYdOIu34vZdzDYE","CAACAgUAAxkBAAEwZzVncS7ZtMeLY-tTtf_EkL5rPkgYzQACqhgAAun6MVZwKQMcjNt6tDYE","CAACAgUAAxkBAAEwZzdncS7iC0uKOuHNBExV5W_MtNGq4gACBRIAApsAATBW8Fk7YoqBZs02BA","CAACAgUAAxkBAAEwZztncS7vd5WdrM8u1eMW91fG4S5ISAACXxUAAkp4YVeJ6WJ1M7OaYTYE"]

    time_key = int(now.strftime("%Y%m%d%H%M%S"))
    random.shuffle(sm_unglam)
    
    file_id = sm_unglam[time_key%len(sm_unglam)]

    bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=reminder, parse_mode="Markdown")
    bot.send_sticker(chat_id=chat_id,message_thread_id=message_thread_id,sticker=file_id)
