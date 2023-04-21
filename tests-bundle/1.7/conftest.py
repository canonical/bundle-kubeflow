import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service



@pytest.fixture(scope='session')
def driver(request):
    """Set up webdriver fixture."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary = "/snap/bin/firefox"

    # must create path,
    # see https://github.com/mozilla/geckodriver/releases/tag/v0.31.0
    os.environ["TMPDIR"] = "~/tmp"
    Path("~/tmp").mkdir(parents=True, exist_ok=True)

    # must have linked snap geckodriver to ~/bin
    # see https://stackoverflow.com/a/74405816/7453765
    service = Service(executable_path="~/bin/firefox.geckodriver")
    driver = webdriver.Firefox(options=options, service=service)
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.implicitly_wait(10)

    yield driver
    driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Set up a hook to be able to check if a test has failed."""
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function", autouse=True)
def failed_check(request):
    """Check if a test has failed and take a screenshot if it has."""
    yield
    if request.node.rep_setup.passed:
        if request.node.rep_call.failed:
            driver = request.node.funcargs['driver']
            take_screenshot(driver, request.node.name)
            print("executing test failed", request.node.nodeid)


def take_screenshot(driver, node_name):
    time.sleep(1)
    Path("screenshots").mkdir(parents=True, exist_ok=True)
    file_name = f'screenshots/{node_name}_{datetime.today().strftime("%m-%d_%H:%M")}.png'
    driver.save_screenshot(file_name)
