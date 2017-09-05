from bs4 import BeautifulSoup
import dryscrape
import time
import schedule
from re                   import sub
from nltk.sentiment.vader import SentimentIntensityAnalyzer
starttime=time.time()
from bs4 import BeautifulSoup
import requests

url="https://www.nseindia.com/live_market/dynaContent/live_watch/pre_open_market/pre_open_market.htm"

# It needs NLTK and Vader Analyzer installed
# Write crons to run it automatically at 9:08 everyday

def get_premarket_volume():
    session = dryscrape.Session()
    session.visit(url)
    response = session.body()
    soup = BeautifulSoup(response, 'html.parser')
    right_table = soup.find('table', {'id': 'preOpenNiftyTab'})
    rows = []
    for row in right_table.find_all('tr'):
        rows.append(
            [" ".join(val.text.encode('utf8').replace(" NFO", "").replace(" NSE", "").replace(" MCX", "")
                      .replace(",","").split()) for val in row.find_all('td')])

    sorted_rows = sorted(rows[2:], key=lambda x: float(x[7]), reverse=True)
    top_stocks=[]
    for row in sorted_rows[:10]:
        top_stocks.append(row[0])
        sc.api_call(
            "chat.postMessage",
            channel="@dexter",
            text='Volume - Stock:{} Volume:{} Change%:{}'.format(row[0], row[7], row[5]),
            as_user=False
        )
    return top_stocks

def filter(text):
    text = text.lower()
    text = sub("[0-9]+", "number", text)
    text = sub("#", "", text)
    text = sub("\n", "", text)
    text = text.replace('$', '@')
    text = sub("@[^\s]+", "", text)
    text = sub("(http|https)://[^\s]*", "", text)
    text = sub("[^\s]+@[^\s]+", "", text)
    text = sub('[^a-z A-Z]+', '', text)
    return text

def similarityScore(s1, s2):
    if len(s1) == 0: return len(s2)
    elif len(s2) == 0: return len(s1)
    v0 = [None]*(len(s2) + 1)
    v1 = [None]*(len(s2) + 1)
    for i in range(len(v0)):
        v0[i] = i
    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        for j in range(len(v0)):
            v0[j] = v1[j]
    return 100-((float(v1[len(s2)])/(len(s1)+len(s2)))*100)

def sentimentScore(texts):
    scores = []
    for text in texts:
        score = SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
        if score != 0: scores.append(score)
    try: return round(sum(scores)/len(scores),3)
    except ZeroDivisionError: return 0

def get_google_news(scrip):
    url='https://www.google.com/finance/company_news?q=NSE%3A'+scrip
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    right_table = soup.find_all('span', {'class': 'name'})

    rows = []

    for row in right_table:
        rows.append(filter(row.find('a').text.encode('utf8')))

    return rows



def wakeup():
    for stock in get_premarket_volume():
        news = get_google_news(stock)
        text='sentiment - Stock: {} score:{}'.format(stock, sentimentScore(news))
        print( text )
        


if __name__ == '__main__':
    wakeup()