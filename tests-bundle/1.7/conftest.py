import time
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver as selenium_webdriver

# we must use Chrome since shadow DOM is not supported by Firefox
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.utils import ChromeType


@pytest.fixture(scope='session')
def driver(request):
    """Set up webdriver fixture."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager(cache_valid_range=5).install())

    print("Driver to call")
    print(Path(service.path).exists())


    driver = selenium_webdriver.Chrome(options=chrome_options, service=service)
    print(1)
    driver.set_window_size(1920, 1080)
    print(2)
    driver.maximize_window()
    print(3)
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
