from subprocess import check_output
from ipaddress import ip_address
import pytest
import yaml
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def polymer_is_trash(elems):
    """Workaround for web components breaking querySelector.

    Because someone thought it was a good idea to just yeet the moral equivalent
    of iframes everywhere over a single page 🤦
    """

    selectors = '").shadowRoot.querySelector("'.join(elems)
    return 'return document.querySelector("' + selectors + '")'


@pytest.mark.full
@pytest.mark.lite
def test_login():
    status = yaml.load(check_output(['juju', 'status', '--format=yaml']))
    endpoint = status['applications']['istio-ingressgateway']['address']
    try:
        ip_address(endpoint)
        endpoint += '.xip.io'
    except ValueError:
        pass
    url = f'http://{endpoint}/'
    output = check_output(['juju', 'config', 'dex-auth', 'static-password'])
    password = output.decode('utf-8').strip()

    options = Options()
    options.add_argument("--headless")
    with webdriver.Firefox(options=options) as driver:
        wait = WebDriverWait(driver, 30, 1, (JavascriptException,))
        try:
            driver.get(url)
            driver.find_element_by_id("login").send_keys("admin")
            driver.find_element_by_id("password").send_keys(password)
            driver.find_element_by_tag_name("form").submit()

            # Ensure that main page loads properly
            script = polymer_is_trash(['main-page', 'dashboard-view', '#Quick-Links'])
            wait.until(lambda x: x.execute_script(script))

            # Navigate to Jupyter frontend
            script = polymer_is_trash(
                ['main-page', 'iframe-link[href=\'/jupyter/?ns=admin\'] .menu-item']
            )
            wait.until(lambda x: x.execute_script(script))
            driver.execute_script(script + '.click()')

            # Click "New Server" button
            script = polymer_is_trash(['main-page', 'iframe-container', 'iframe'])
            script += ".contentWindow.document.body.querySelector('#add-nb')"
            wait.until(lambda x: x.execute_script(script))
            driver.execute_script(script + '.click()')

            # Enter server name
            script = polymer_is_trash(['main-page', 'iframe-container', 'iframe'])
            script += ".contentWindow.document.body.querySelector('#mat-input-0')"
            wait.until(lambda x: x.execute_script(script))
            driver.execute_script(script + '.value = "foobar"')
            driver.execute_script(script + '.dispatchEvent(new Event("input"))')

            # Submit form
            script = polymer_is_trash(['main-page', 'iframe-container', 'iframe'])
            script += ".contentWindow.document.body.querySelector('form').submit()"
            driver.execute_script(script)
        except Exception:
            driver.get_screenshot_as_file('/tmp/selenium.png')
            raise
