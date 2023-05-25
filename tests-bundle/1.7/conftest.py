import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

DEBUG = os.environ.get("DEBUG_KF", False)


@pytest.fixture(scope='session')
def driver(request):
    """Set up webdriver fixture."""
    options = Options()
    if not DEBUG:
        print("Running in headless mode")
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    else:
        options.log.level = "trace"

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/snap/bin/firefox"

    # must create path,
    # see https://github.com/mozilla/geckodriver/releases/tag/v0.31.0
    tmp_user = Path("~/tmp").expanduser()
    os.environ["TMPDIR"] = str(tmp_user)
    tmp_user.mkdir(parents=True, exist_ok=True)

    service = Service(GeckoDriverManager().install())
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
    Path("sel-screenshots").mkdir(parents=True, exist_ok=True)
    file_name = f'sel-screenshots/{node_name}_{datetime.today().strftime("%m-%d_%H-%M")}.png'
    print(f"Taking screenshot: {file_name}")
    driver.save_screenshot(file_name)
