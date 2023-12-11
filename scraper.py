import time
import aiohttp
import requests
from bs4 import BeautifulSoup
import discord
from dotenv import dotenv_values
import asyncio

# Load configuration from .env file
config = dotenv_values(".env")

# Discord bot token
TOKEN = config["DISCORD_TOKEN"]
TARGET_USER_ID = int(config["TARGET_USER_ID"])

# URL and course title
url = "https://web.csulb.edu/depts/enrollment/registration/class_schedule/Spring_2024/By_Subject/CECS.html"
course_title = "COMPUTER SCI SENIOR PROJECT I"
# course_title = "INTRODUCTION TO CECS"

# Initialize Discord bot
bot = discord.Client(intents=discord.Intents.default())

async def send_message(user_id: int, message=None):
    """
    Asynchronously sends a message to a user on Discord.

    Args:
    user_id (int): Discord user ID to whom the message is sent.
    message (str): Message content. Defaults to a predefined message.
    """
    user = await bot.fetch_user(user_id)
    message = message or "This Message is sent via send_message"
    await user.send(message)
    

async def monitor_course_sections(url, course_title, check_interval=60):
    """
    Asynchronously monitors the number of sections for a course.
    """
    while True:
        sections = await fetch_course_sections(url, course_title)
        if len(sections) > 3:
            print("Alert: More than 3 sections found for the course!")
            break
        await asyncio.sleep(check_interval)

def get_value_of_key_starting_with(dict_data, start_string):
    # Iterate through each key in the dictionary
    for key in dict_data.keys():
        # Check if the key starts with the specified string
        if key.startswith(start_string):
            # Return the value associated with the key
            return dict_data[key]
    # Return None if no key starts with the specified string
    return None


def parse_sections_table(table):
    """
    Parses the sections table and returns a list of dictionaries with section details.
    """
    sections = []
    headers = [th.text.strip() for th in table.find_all('th', scope='col')]

    # Debugging: Print headers to see what they are
    print("Table Headers:", headers)

    for row in table.find_all('tr')[1:]:  # Skipping the header row
        cells = row.find_all(['th', 'td'])
        section_info = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
        sections.append(section_info)

    formatted = []

    for section in sections:
        # Find the correct index for 'Open Seats' or a similar header
        open_seats_index = next((i for i, header in enumerate(headers) if "OPEN SEATS" in header.upper()), None)
        if open_seats_index is not None:
            open_seats_cell = cells[open_seats_index]
            dot_element = open_seats_cell.find(class_="dot")
            open_seats = 1 if dot_element else 0
        else:
            open_seats = 0  # Default value if header is not found

        formatted_section = {
            "Section": section['SEC.'],
            "Class Number": section['CLASS #'],
            "Instructor": section['INSTRUCTOR'],
            "Open Seats": open_seats,
        }
        formatted.append(formatted_section)

    return formatted



def print_dict(dict_data):
    """
    Prints the dictionary in a formatted way.
    
    Args:
    dict_data (dict): The dictionary to print.
    """
    for key, value in dict_data.items():
        print(f"\t{key}: {value}")

async def fetch_course_sections(url, course_title):
    """
    Asynchronously fetches and prints the sections table for a specific course title from the given URL.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print("Failed to retrieve the web page.")
                return []

            # Parse the HTML content
            soup = BeautifulSoup(await response.text(), 'html.parser')

    # Find the course header div
    course_header = soup.find(lambda tag: tag.name == "div" and tag.get("class", []) == ["courseHeader"] and course_title in tag.text)
    if course_header:
        # Find the sibling table element
        sections_table = course_header.find_next_sibling('table')
        if sections_table:
            sections = parse_sections_table(sections_table)
            open_seats = 0
            for section in sections:
                print(section)
                open_seats += section["Open Seats"]
                if section["Open Seats"] > 0:
                    print("Open seats available!")
                    print_dict(section)
                    await send_message(TARGET_USER_ID, f'Open seat(s) for {course_title} -- {section["Section"]}\n> Course Number: `{section["Class Number"]}`\n> Instructor: {section["Instructor"]}\n[Schedule of Courses]({url})')
            if open_seats == 0:
                print(f'No open seats available on {time.strftime("%H:%M:%S")} at {time.strftime("%d/%m/%Y")}')
                # await send_message(TARGET_USER_ID, f'No open seats available on {time.strftime("%H:%M:%S")} at {time.strftime("%d/%m/%Y")}')
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"{open_seats} seats available for {course_title} (Updated {time.strftime('%H:%M')} on {time.strftime('%A')})")
            await bot.change_presence(status=discord.Status.idle, activity=activity)
        
                
        else:
            print(f"No sections table found for '{course_title}'.")
    else:
        print(f"Course with title '{course_title}' not found.")
    return sections

@bot.event
async def on_ready():
    """
    Called when the bot is ready. Prints bot's username.
    """
    print(f'{bot.user} is now running')
    asyncio.create_task(monitor_course_sections(url, course_title))  # Correctly create a task for monitoring

bot.run(TOKEN)