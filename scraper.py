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
    
    Args:
    table (Tag): The BeautifulSoup Tag object of the table to be parsed.
    
    Returns:
    list[dict]: A list of dictionaries, each containing details of a section.
    """
    sections = []
    headers = [th.text.strip() for th in table.find_all('th', scope='col')]

    for row in table.find_all('tr')[1:]:  # Skipping the header row
        cells = row.find_all(['th', 'td'])
        section_info = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
        sections.append(section_info)

    formatted = []

    for section in sections:
        open_seats = 0 if get_value_of_key_starting_with(section, "OPEN SEATS") == '' else int(get_value_of_key_starting_with(section, "OPEN SEATS"))
        formatted_section = {
            "Section": section['SEC.'],
            "Class Number": section['CLASS #'],
            "Instructor": section['INSTRUCTOR'],
            "Open Seats": open_seats, # Open seats
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
                open_seats += section["Open Seats"]
                if section["Open Seats"] > 0:
                    print("Open seats available!")
                    print_dict(section)
                    await send_message(TARGET_USER_ID, f'Open seats available!\n{section["Section"]}\n{section["Class Number"]}\n{section["Instructor"]}\n{section["Open Seats"]}')
            if open_seats == 0:
                print(f'No open seats available on {time.strftime("%H:%M:%S")} at {time.strftime("%d/%m/%Y")}')
                await send_message(TARGET_USER_ID, f'No open seats available on {time.strftime("%H:%M:%S")} at {time.strftime("%d/%m/%Y")}')
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"{open_seats} seats available (Updated {time.strftime('%H:%M')} on {time.strftime('%A')})")
            await bot.change_presence(status=discord.Status.idle, activity=activity)
        
                
        else:
            print(f"No sections table found for '{course_title}'.")
    else:
        print(f"Course with title '{course_title}' not found.")
    return sections

# URL and course title
url = "https://web.csulb.edu/depts/enrollment/registration/class_schedule/Spring_2024/By_Subject/CECS.html"
course_title = "COMPUTER SCI SENIOR PROJECT I"

@bot.event
async def on_ready():
    """
    Called when the bot is ready. Prints bot's username.
    """
    print(f'{bot.user} is now running')
    asyncio.create_task(monitor_course_sections(url, course_title))  # Correctly create a task for monitoring

bot.run(TOKEN)