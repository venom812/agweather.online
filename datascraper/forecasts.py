from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


######################################
# FORECAST SOURCES SCRAPER FUNCTIONS #
######################################
# !To provide a call function from Forecast template class method
# "scrap_all_forecasts" their names must be the same as in Database:
# table "datascraper_forecastsource", col:"id"
def rp5(start_datetime, url):

    # Scraping html content from source
    soup = get_soup(url)
    ftab = soup.find(id='ftab_content')

    # Parsing start date from source html page
    start_date_from_source = ftab.find(
        'span', class_="weekDay").get_text().split(',')[-1].split()
    start_date_from_source = func_start_date_from_source(
        month=month_rusname_to_number(start_date_from_source[1][:3]),
        day=int(start_date_from_source[0]),
        req_start_datetime=start_datetime
    )

    # Parsing time row from source
    time_row = ftab.find('tr', class_="forecastTime").find_all('td')[1:-1]
    time_row = [int(t.get_text()) for t in time_row]

    # Parsing weather parameters rows from source:
    # Temperature
    temp_row = ftab.find('a', class_='t_temperature')
    temp_row = temp_row.parent.parent.find_all('td')[1:-1]
    temp_row = [int(t.find('div', class_='t_0').get_text()) for t in temp_row]
    # Pressure
    press_row = ftab.find('a', class_='t_pressure')
    press_row = press_row.parent.parent.find_all('td')[1:-1]
    press_row = [
        int(t.find('div', class_='p_0').get_text()) for t in press_row]
    # Wind velocity
    wind_vel_row = ftab.find('a', class_='t_wind_velocity')
    wind_vel_row = wind_vel_row.parent.parent.find_all('td')[1:-1]
    wind_vel_row = [w.find('div', class_='wv_0') for w in wind_vel_row]
    wind_vel_row = [int(w.get_text()) if w else 0 for w in wind_vel_row]
    # Merge parameters from source into one tuple
    raw_data = (temp_row, press_row, wind_vel_row)

    return json_data_gen(
        start_datetime, start_date_from_source, time_row, raw_data)


def yandex(start_datetime, url):

    # Scraping html content from source
    soup = get_soup(url)
    ftab = soup.find('div', class_='content')

    # Parsing start date from source html page
    start_datetime = start_datetime.replace(hour=9, minute=0, second=0,
                                            microsecond=0)  # Morning
    start_date_from_source = func_start_date_from_source(
        month=month_rusname_to_number(ftab.find(
            'span', class_='forecast-details__day-month').get_text()),
        day=int(ftab.find(
            'strong', class_='forecast-details__day-number').get_text()),
        req_start_datetime=start_datetime
    )

    # Parsing weather parameters rows from source:
    # Temperature
    temp_row = ftab.find_all('div', class_='weather-table__temp')
    temp_row = [t.get_text() for t in temp_row]
    # Conversion of the temperature of the form "+6...+8"
    # to the average value
    temp_row = [t.replace(chr(8722), '-').split('…') for t in temp_row]
    temp_row = [[int(i) for i in t] for t in temp_row]
    temp_row = [int(round(sum(t)/len(t))) for t in temp_row]
    # Pressure
    press_row = ftab.find_all('td', class_='weather-table__' +
                              'body-cell_type_air-pressure')
    press_row = [int(p.get_text()) for p in press_row]
    # Wind velocity
    wind_vel_row = ftab.find_all('span', class_="wind-speed")
    wind_vel_row = [int(round(float(w.get_text().replace(',', '.')), 0))
                    for w in wind_vel_row]
    # Merge parameters from source into one tuple
    raw_data = (temp_row, press_row, wind_vel_row)

    # Parsing time row from source
    time_row = [9, 15, 21, 3]*(len(temp_row)//4)

    return json_data_gen(
        start_datetime, start_date_from_source, time_row, raw_data)


def meteoinfo(start_datetime, url):

    # Scraping html content from source
    soup = get_soup(url)
    ftab = soup.find('div', class_='hidden-desktop')

    # Parsing start date from source html page
    start_datetime = start_datetime.replace(minute=0, second=0, microsecond=0)
    start_date_from_source = ftab.find('nobr')
    start_hour = start_date_from_source.parent.next_sibling.get_text()
    start_hour = 15 if start_hour.strip().lower() == 'день' else 3
    start_date_from_source = start_date_from_source.get_text()
    start_date_from_source = func_start_date_from_source(
        month=month_rusname_to_number(start_date_from_source),
        day=int(re.findall(r'\d+', start_date_from_source)[0]),
        req_start_datetime=start_datetime
    )

    # Parsing weather parameters rows from source:
    # Temperature
    temp_row = ftab.find_all('span', class_='fc_temp_short')
    temp_row = [int(t.get_text().rstrip('°')) for t in temp_row]
    # Wind velocity
    wind_vel_row = ftab.find_all('i')
    press_row = wind_vel_row[:]
    wind_vel_row = [int(w.next_sibling.get_text()) for w in wind_vel_row]
    # Pressure
    press_row = [int(p.parent.next_sibling.get_text()) for p in press_row]

    # Parsing time row from source
    time, time_row = start_hour, []
    for t in temp_row:
        time_row.append(time)
        time = 15 if time == 3 else 3

    # Merge parameters from source into one tuple
    raw_data = (temp_row, press_row, wind_vel_row)

    return json_data_gen(
        start_datetime, start_date_from_source, time_row, raw_data)


def foreca(start_datetime, url: str):

    # Scraping html content from source first day page
    soup = get_soup(url)

    # print(soup)
    ftab = soup.find('div', class_='page-content')

    # Parsing start date from source html page
    start_date_from_source = ftab.find('div', class_='date').get_text().split()
    start_date_from_source = func_start_date_from_source(
        month=month_rusname_to_number(start_date_from_source[1][:3]),
        day=int(start_date_from_source[0]),
        req_start_datetime=start_datetime
    )

    # Parsing next days urls from source first day page
    domain = url[:url.find('/', 8)]
    next_days_urls = ftab.find('ul', class_='days').find_all('a')[1:]
    next_days_urls = [domain + nd.get('href') for nd in next_days_urls]
    # print(next_days_urls)

    # Scraping tables data to array
    ftabs = [ftab] + [get_soup(ndu).find('div', class_='page-content') for
                      ndu in next_days_urls]

    raw_data = [[] for i in range(4)]
    # Parsing from saved tables
    for ftab in ftabs:
        # Parsing time row from source
        ftab = ftab.find('div', class_='hourContainer')
        time_row = ftab.find_all('span', class_='time_24h')
        time_row = [int(t.get_text()) for t in time_row]
        raw_data[0].extend(time_row)

        # Parsing weather parameters rows from source pages:
        # Temperature
        temp_row = ftab.find_all('span', class_='t')
        temp_row = [int(t.find('span', class_='temp_c').
                        get_text()) for t in temp_row]
        raw_data[1].extend(temp_row)
        # Pressure
        press_row = ftab.find_all('span', class_='value pres pres_mmhg')
        press_row = [int(round(float(p.get_text()))) for p in press_row]
        raw_data[2].extend(press_row)
        # Wind velocity
        wind_vel_row = ftab.find_all('span', class_='windSpeed')
        wind_vel_row = [int(w.find('span', class_='value wind wind_ms').
                            get_text().split()[0]) for w in wind_vel_row]
        raw_data[3].extend(wind_vel_row)

    # for i in raw_data:
    #     print(i)

    return json_data_gen(
        start_datetime, start_date_from_source, raw_data[0], raw_data[1:])


########
# MISC #
########


def get_soup(url):
    """Scraping html content from source with the help of Selenium library"""

    driver = init_selenium_driver()

    # try:
    driver.get(url=url)
    src = driver.page_source
    # except Exception as _ex:
    #     print(_ex)
    # finally:
    #     print(url)
    driver.close()
    driver.quit()

    # return src
    return BeautifulSoup(src, "lxml")


def init_selenium_driver():
    """Selenium driver initialization"""

    # create a new Service instance and specify path to Chromedriver executable
    service = ChromeService(executable_path=ChromeDriverManager().install())

    # create a ChromeOptions object
    options = webdriver.ChromeOptions()
    # run in headless mode
    options.add_argument("--headless")
    # disable the AutomationControlled feature of Blink rendering engine
    options.add_argument('--disable-blink-features=AutomationControlled')
    # disable pop-up blocking
    options.add_argument('--disable-popup-blocking')
    # start the browser window in maximized mode
    options.add_argument('--start-maximized')
    # disable extensions
    options.add_argument('--disable-extensions')
    # disable sandbox mode
    options.add_argument('--no-sandbox')
    # disable shared memory usage
    options.add_argument('--disable-dev-shm-usage')

    # Waits for page to be interactive
    options.page_load_strategy = 'eager'

    # create a driver instance
    driver = webdriver.Chrome(service=service, options=options)
    # Change the property value of the navigator for webdriver to undefined
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', \
                          {get: () => undefined})")

    user_agents = [
        # Add your list of user agents here
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 \
            (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 \
            (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    ]

    # select random user agent
    user_agent = random.choice(user_agents)

    # pass in selected user agent as an argument
    options.add_argument(f'user-agent={user_agent}')

    # enable stealth mode
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    # caps = DesiredCapabilities().CHROME
    # # caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    # caps["pageLoadStrategy"] = "eager"  # Waits for page to be interactive
    # # caps["pageLoadStrategy"] = "none"   # Do not wait for full page load

    return driver


def func_start_date_from_source(month, day, req_start_datetime):
    """Calculate the starting date of the forecast source."""
    year = req_start_datetime.year
    # Processing the transition through the new year
    if req_start_datetime.month == 12 and month == 1:
        year += 1

    return datetime(year, month, day, tzinfo=req_start_datetime.tzinfo)


def month_rusname_to_number(name):
    """Translate russian month name to its number."""
    month_tuple = ('', 'янв', 'фев', 'мар', 'апр', 'мая', 'июн',
                   'июл', 'авг', 'сен', 'окт', 'ноя', 'дек')
    name = name.strip().lower().split(' ')[-1][:3]
    if name == 'май':
        return 5
    return month_tuple.index(name)


def intp_linear(xa, xc, xb, ya, yb):
    """Linear interpolation."""
    return round((xc-xa)/(xb-xa)*(yb-ya)+ya)


def json_data_gen(start_datetime, start_date_from_source,
                  time_row_from_source, raw_data):
    """Recalculating forecast data from source datetime row to required row."""

    # Generating datetime row from html source
    datetime_row_from_source = []
    for i, hour in enumerate(time_row_from_source):
        if i != 0 and hour < time_row_from_source[i-1]:
            start_date_from_source += timedelta(days=1)
        datetime_row_from_source.append(start_date_from_source
                                        + timedelta(hours=hour))

    # Generating json record
    data_json, datetime_ = [[] for i in raw_data], start_datetime
    datetime_step = timedelta(hours=6)
    # index = 0
    while datetime_ <= datetime_row_from_source[-1]:
        for i, dt in enumerate(datetime_row_from_source):
            if (i == 0 and datetime_ < dt) or dt - datetime_ >= datetime_step:
                [data_json[p].append(None) for p in range(len(raw_data))]
            elif datetime_ == dt:
                [data_json[j].append(p[i]) for j, p in enumerate(raw_data)]
            elif datetime_ < dt:
                [data_json[j].append(intp_linear(
                    datetime_row_from_source[i-1].timestamp(),
                    datetime_.timestamp(),
                    dt.timestamp(),
                    p[i-1],
                    p[i])) for j, p in enumerate(raw_data)]
            else:
                continue

            del datetime_row_from_source[:i]
            for p in range(len(raw_data)):
                del raw_data[p][:i]
            break

        datetime_ += datetime_step

    return data_json
