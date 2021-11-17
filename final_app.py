import time
import requests
import os
from bs4 import BeautifulSoup
from twilio.rest import Client
from googlesearch import search


class CryptoNotificationsSender:

    def __init__(self):
        self.coinmarket_api_key = os.environ.get('COINMARKET_API_KEY')
        self.twilio_number = os.environ.get('TWILIO_NUMBER')
        self.verified_number = os.environ.get('VERIFIED_NUMBER')
        self.twilio_sid = os.environ.get('TWILIO_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.cryptowallet = ['SLP', 'DOGE', 'TRX']
        self.changed_cryptocurrencies = []
        self.percent_changes = []
        self.all_titles_list = []
        self.all_links_list = []
        self.message_to_user = ''

    # Iterate over my wallet, get data from CoinmarketCap

    def get_cryptocurrency_data(self):
        for cryptocurrency in self.cryptowallet:
            url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            parameters = {'symbol': cryptocurrency}
            headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': self.coinmarket_api_key}
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(url, params=parameters)
            data = response.json()
            percent_change_1h = data['data'][cryptocurrency]['quote']['USD']['percent_change_1h']
            self.percent_changes.append(round(percent_change_1h, 1))
            self.changed_cryptocurrencies = list(zip(self.cryptowallet, self.percent_changes))
        return self.changed_cryptocurrencies

    # This function iterates over all changed cryptocurrencies and checks if their percent if more 4% or less than 4%
    # If percent is between -5% and 5% --> It removes this tuple from list of changed cryptocurrencies.

    def check_for_changes(self):
        self.changed_cryptocurrencies = [i for i in self.changed_cryptocurrencies if i[1] > 5 or i[1] < -5]
        if len(self.changed_cryptocurrencies) != 0:
            return True, self.changed_cryptocurrencies
        else:
            return False

    # This function makes requests to Google and looks for titles about specific cryptocurrency.

    def check_recent_news(self, cryptocurrency):
        ticker = cryptocurrency[0]
        google_url = "https://www.google.com/search?q=" + ticker + "+crypto&hl=en&tbm=nws&tbs=sbd:1"
        response = requests.get(google_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        all_titles = soup.find_all(class_='BNeawe vvjwJb AP7Wnd')
        self.all_titles_list = [title.text for title in all_titles[:3]]
        return self.all_titles_list

    # This function is responsible for looking for links using specific titles. It uses GoogleSearch module.

    def get_news_links(self):
        self.all_links_list = [search(term=title, lang='en')[1] for title in self.all_titles_list]
        return self.all_links_list

    # This function builds a message using list of news and list of links.

    def build_a_message(self, element, news_arr, links_arr):
        name = element[0]
        percent = element[1]
        title = f'{name} changed for {percent}%\n\nThere are the latest news about {name}:\n'
        news = ''.join([f'{str(title)}\n\n' for title in news_arr])
        links = ','.join(links_arr).replace(',', ' \n\n')
        self.message_to_user = f'{title}\n{news}{links}'
        return self.message_to_user

    # This function uses Twilio and it sends a message, that has been built in previous function.

    def send_a_message(self):
        client = Client(self.twilio_sid, self.twilio_auth_token)
        client.messages.create(
            body=self.message_to_user,
            from_=self.twilio_number,
            to=self.verified_number
        )


app = CryptoNotificationsSender()
app.get_cryptocurrency_data()
while True:
    if app.check_for_changes():
        print('Some cryptocurrencies changed. Looking for news and building a message....\n')
        for item in app.changed_cryptocurrencies:
            app.check_recent_news(item)
            app.get_news_links()
            app.build_a_message(item, app.all_titles_list, app.all_links_list)
            app.send_a_message()
        print('I am sleeping and waiting for changes :)\n')
        time.sleep(1800)
    else:
        print('No big changes on the market. Waiting for one more hour.....\n')
        time.sleep(3600)
