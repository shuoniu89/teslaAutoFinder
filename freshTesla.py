'''
>tesla-inventory-price-scraper.py<
@Author: JoPang
@Date: Aug 2023
@Description:

This script scrapes Tesla's car inventory website and alerts the user if a car under a certain price appears.

It can easily be adapted to do other things with the results, such as alert you when a specific car with a specific trim/color/wheel size appears in inventory.

Usage: Go on tesla's inventory and search using the filters you are interested in. Copy the URL and add it to the urls[] array below, with an identifier (city or other)

Run the script. It will show a popup when a car under your price threshold is found.
'''

import json
import pprint
import time
import threading
import re
import smtplib
from email.mime.text import MIMEText

from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from datetime import datetime


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


def send_email(subject, body, to_email):
    # Gmail settings
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    GMAIL_USERNAME = 'notification_sent_from@gmail.com'  # Edit: replace with your Gmail address
    GMAIL_PASSWORD = 'GmailAppPassword'  # Edit: replace with your Gmail password

    # Construct email
    msg = MIMEText(body)
    msg['From'] = GMAIL_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject

    # Connect to Gmail SMTP server and send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USERNAME, to_email, msg.as_string())
        server.close()
        print("Email sent successfully!")
    except Exception as e:
        print("Failed to send email:", e)


import ctypes  # An included library with Python install.

html = None

# Edit: Go to Tesla inventory page, set the search filters to match your need, and paste the link here.
# You can search multiple links together
urls = {
    "Boston": 'https://www.tesla.com/inventory/new/my?TRIM=LRAWD&PAINT=BLUE,SILVER&INTERIOR=PREMIUM_BLACK&WHEELS=NINETEEN&arrangeby=plh&zip=01772&range=200',
}

results_container_selector = 'div.results-container.results-container--grid.results-container--has-results'
delay = 10  # seconds

priceThreshold = 50490  # Edit: set a max price you want to pay

while True:
    for city in urls:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            browser = webdriver.Chrome(options=options)
            print(datetime.now().strftime("%H:%M:%S") + " Searching Tesla's website in " + city)
            browser.get(urls[city])

            # wait for results to be displayed
            WebDriverWait(browser, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector))
            )

        except TimeoutException:
            print('Loading took too much time!')
        else:
            html = browser.page_source
        finally:
            browser.quit()

        if html:
            soup = BeautifulSoup(html, 'lxml')
            cars = []
            for car_html in soup.select_one(results_container_selector).findChildren('article'):
                car = {}

                car['price'] = int(re.sub('[^0-9]', '', car_html.find_next('span', {
                    "class": 'result-purchase-price tds-text--h4'}).text.replace('$', '').replace(',', '')))
                car['base_price'] = int(re.sub('[^0-9]', '', car_html.find_next('span', {
                    "class": 'tds-text--caption result-price-base-price'}).text.replace('$', '').replace(',', '')))
                car['colour'] = \
                    car_html.select('section.result-features.features-grid')[0].select('ul')[1].select('li')[0].text
                car['type'] = car_html.select_one('section.result-header').select_one(
                    'div.result-basic-info').select_one('h3').text
                car['trim'] = \
                    car_html.select_one('section.result-header').select_one('div.result-basic-info').select('div')[
                        0].text
                car['wheels'] = re.sub('[^0-9]', '',
                                       car_html.select('section.result-features.features-grid')[0].select('ul')[
                                           1].select('li')[1].text) + " inch wheels"
                car['exterior'] = \
                    car_html.select('section.result-features.features-grid')[0].select('ul')[1].select('li')[0].text
                car['interior'] = \
                    car_html.select('section.result-features.features-grid')[0].select('ul')[1].select('li')[2].text
                # Edit: this if condition to match your need
                if ('Silver' in car['colour'] and car['base_price'] - car['price'] >= 2000 and car[
                    'price'] <= priceThreshold) or (
                        'Blue' in car['colour'] and car['base_price'] - car['price'] >= 1500 and car[
                    'price'] <= priceThreshold):
                    print(car)
                    cars.append(car)
            if len(cars) > 0:
                msg = '\n\n'.join(['\n'.join([k + ": " + str(v) for k, v in c.items()]) for c in cars])
                send_email("TESLA AUTO FINDER", f"cars:\n{msg}",
                           "email_to_receive_notification@gmail.com")  # Edit this email to receive notifications
                send_email("TESLA AUTO FINDER", f"cars:\n{msg}",
                           "another_email_to_receive_notification@gmail.com")  # Edit this email to receive notifications
            time.sleep(300)  # refresh every 300 seconds
