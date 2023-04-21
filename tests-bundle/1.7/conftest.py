import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

DEBUG = True
if DEBUG:
    firefox_binary = "/snap/bin/firefox"
else:
    firefox_binary = "/snap/firefox/current/firefox.launcher"


@pytest.fixture(scope='session')
def driver(request):
    """Set up webdriver fixture."""
    options = Options()
    if not DEBUG:
        options.add_argument('--headless')
    else:
        options.log.level = "trace"

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = firefox_binary

    # must create path,
    # see https://github.com/mozilla/geckodriver/releases/tag/v0.31.0
    tmp_user = Path("~/tmp").expanduser()
    os.environ["TMPDIR"] = str(tmp_user)
    tmp_user.mkdir(parents=True, exist_ok=True)

    # must have linked snap geckodriver to ~/bin
    # see https://stackoverflow.com/a/74405816/7453765
    bin_user = Path("~/bin").expanduser()
    bin_user.mkdir(parents=True, exist_ok=True)
    source_file = Path("/snap/bin/firefox.geckodriver")
    geckodriver = bin_user / "firefox.geckodriver"
    if not geckodriver.exists():
        geckodriver.symlink_to(source_file)

    executable_path = str(bin_user)
    service = Service(executable_path=executable_path)
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
