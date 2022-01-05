from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import pandas as pd
import pygsheets
import traceback

s = Service("./geckodriver")

options = webdriver.FirefoxOptions()
options.add_argument("--disable-extensions")
options.add_argument("--disable-popup-blocking")
options.add_argument("--profile-directory=Default")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-plugins-discovery")
options.add_argument("user_agent=DN")
options.add_argument('--headless')
options.add_argument("--no-sandbox")

desired = DesiredCapabilities.FIREFOX
# zhlz2zap.default-release-1639056005868
fp = webdriver.FirefoxProfile('./zhlz2zap.default-release-1639056005868')

driver = webdriver.Firefox(service=s, options=options,
                           desired_capabilities=desired, firefox_profile=fp)

baseLink = "https://optimize.google.com/optimize/home/"

print("-------")
print(baseLink)
print("-------")
driver.get(baseLink)
driver.implicitly_wait(5)

driver.get_screenshot_as_file("screenshot.png")

try:

    # opt-account-card-container-list
    WebDriverWait(driver, 10).until(ec.element_to_be_clickable(
        (By.XPATH, '//tr[contains(@class, "opt-account-card-container-list")]')))

    trsContainer = driver.find_elements_by_css_selector(
        '.opt-account-card-container-list')

    data = []
    containerLinks = []
    containerNames = []
    detailLinks = []

    for trContainer in trsContainer:
        tdsContainer = trContainer.find_elements_by_tag_name('td')

        containerName = tdsContainer[0].text
        containerLink = tdsContainer[0].find_element_by_tag_name(
            'a').get_attribute('href')

        print("-------")
        print(containerLink)
        containerLinks.append(containerLink)
        containerNames.append(containerName)

    for j in range(len(containerLinks)):
        containerLink = containerLinks[j]
        containerName = containerNames[j]
        driver.get(containerLink)

        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(
            (By.XPATH, '//tr[@ng-if="ctrl.getExperiments(experimentStatus).length"]')))

        trs = driver.find_elements_by_css_selector(
            '[ng-if="ctrl.getExperiments(experimentStatus).length"]')

        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')

            if len(tds) == 6:
                type = tds[1].text
                # can contain date, a number or a -
                started = tds[3].text
                ended = tds[4].text

                # ignore running experiments, only focus on finished
                if started.isnumeric() or started == "-":
                    continue

                if(type != "A/B"):
                    continue

                data.append({
                    'container': containerName,
                    'type': type,
                    'started': started,
                    'ended': ended
                })

                print('------------')
                print(containerName)
                print(type)
                print(started)
                print(ended)

                detailLinks.append(tds[0].find_element_by_tag_name(
                    'a').get_attribute('ng-href'))

                time.sleep(1)

    print('Going over detailLinks')
    for i in range(len(detailLinks)):
        link = detailLinks[i].replace('/report', '')

        print('------------')
        print(baseLink+link)
        driver.get(baseLink+link)

        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[contains(@class, "opt-ga-tracking-id")]')))

        # experimentId = driver.find_element_by_xpath(
        #     '//*[contains(@class, "opt-ga-tracking-id")]').text

        divs = driver.find_elements_by_xpath(
            '//div[contains(@class, "opt-measurement-column")]/div')

        data[i]['property'] = divs[1].text
        data[i]['view'] = divs[3].text
        data[i]['experimentId'] = divs[5].text
        time.sleep(1)

    print(data)

    gc = pygsheets.authorize(
        service_file='./startandenddateautomation-494e73c92522.json')
    df = pd.DataFrame(data)
    sh = gc.open('Start End Date Automation')
    wks = sh[0]
    wks.set_dataframe(df, (1, 1))

except Exception as e:
    traceback.print_exc()
    print(e)

driver.quit()

print("--- DONE ---")
