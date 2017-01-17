import datetime
import lxml.html
import os
import pytz
import requests

from flask import Flask, redirect, render_template, request

app = Flask(__name__)

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead - 7)

@app.route("/")
def index():

    # get the weather
    token = os.environ.get("WEATHER_TOKEN")
    res = requests.get("http://api.openweathermap.org/data/2.5/forecast/daily?q=Cambridge,MA&cnt=2&units=imperial", params={"APPID": token})
    if res.status_code == 200:
        data = res.json()
        weather_status = data["list"][1]["weather"][0]["main"]
        low = data["list"][1]["temp"]["min"]
        high = data["list"][1]["temp"]["max"]
        timestamp = data["list"][1]["dt"]
        date = datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.timezone("America/New_York")).strftime('%m-%d-%Y')
        weather = {
            "timestamp": date,
            "status": weather_status,
            "low": low,
            "high": high
        }
    else:
        weather = None

    return render_template("index.html", weather=weather)

@app.route("/extract/")
def extract():
    url = request.args.get("url")
    res = requests.get(url)
    if res.status_code != 200:
        return "ERROR: Could not parse website."

    contents = lxml.html.fromstring(res.text)
    text = contents.get_element_by_id("text")

    # get headline
    headline = contents.get_element_by_id("top")
    headline = headline.text

    # remove all the images
    images = text.find_class("shortcodes-object")
    for image in images:
        image.drop_tree()

    ids_to_remove = ["subscribe-link", "previous-article-bottom", "article-tags"]
    for id_to_remove in ids_to_remove:
        elt = text.get_element_by_id(id_to_remove)
        if elt is not None:
            elt.drop_tree()

    classes_to_remove = ["article-recommended-container"]
    for class_to_remove in classes_to_remove:
        for element in text.find_class(class_to_remove):
            element.drop_tree()

    res = "<h1>" + str(headline) + "</h1>" + lxml.html.tostring(text).decode("utf-8")

    return res

@app.route("/crossword/")
def crossword():
    # get the date of the most recent Monday
    d = datetime.datetime.now()
    next_monday = next_weekday(d, 0)
    date_string = next_monday.strftime("%y%m%d")
    url = "http://bbs.amuniversal.com/web/content/UFS_Puzzles/Todays_Crossword_Dailies/dax{}_week.zip".format(date_string)
    return redirect(url)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
