# web_scraper.py

import time
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
import discord


bot = commands.Bot(command_prefix='!')

user = bot.get_user(381870129706958858)

@bot.command()
async def DM(ctx, user: discord.User, *, message=None):
    message = message or "This Message is sent via DM"
    await user.send(message)

bot.run(TOKEN)

def monitor_course_sections(url, course_title, check_interval=60):
    """
    Monitors the number of sections for a course and alerts if more than 2 sections are found.

    Args:
    url (str): The URL to scrape.
    course_title (str): The title of the course to monitor.
    check_interval (int): Time interval in seconds between checks.
    """
    while True:
        sections = fetch_course_sections(url, course_title)
        if len(sections) > 3:
            print("Alert: More than 3 sections found for the course!")
            break

        time.sleep(check_interval)

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

def fetch_course_sections(url, course_title):
    """
    Fetches and prints the sections table for a specific course title from the given URL.
    
    Args:
    url (str): The URL to scrape.
    course_title (str): The title of the course to look for.
    """
    # Fetch the HTML content from the URL
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the web page.")
        return

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

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
                    user.send(section)
            if open_seats == 0:
                print(f'No open seats available on {time.strftime("%H:%M:%S")} at {time.strftime("%d/%m/%Y")}')
                user.send("No seats available!")
        
                
        else:
            print(f"No sections table found for '{course_title}'.")
    else:
        print(f"Course with title '{course_title}' not found.")
    return sections

# URL and course title
url = "https://web.csulb.edu/depts/enrollment/registration/class_schedule/Spring_2024/By_Subject/CECS.html"
course_title = "COMPUTER SCI SENIOR PROJECT I"

# Fetch and display course sections
monitor_course_sections(url, course_title)