from ipaddress import ip_address
from pathlib import Path
from random import choices
from shutil import which
from string import ascii_lowercase
from subprocess import check_output
from time import sleep
from urllib.parse import urlparse

import pytest
import yaml
from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver


def fix_queryselector(elems):
    """Workaround for web components breaking querySelector.

    Because someone thought it was a good idea to just yeet the moral equivalent
    of iframes everywhere over a single page 🤦

    Shadow DOM was a terrible idea and everyone involved should feel professionally
    ashamed of themselves. Every problem it tried to solved could and should have
    been solved in better ways that don't break the DOM.
    """

    selectors = '").shadowRoot.querySelector("'.join(elems)
    return 'return document.querySelector("' + selectors + '")'


def evaluate(doc, xpath):
    result_type = 'XPathResult.FIRST_ORDERED_NODE_TYPE'
    return f'return {doc}.evaluate("{xpath}", {doc}, null, {result_type}, null).singleNodeValue'


@pytest.fixture()
def driver(request):
    proxy = request.config.option.proxy
    url = request.config.option.url
    password = request.config.option.password
    headful = request.config.option.headful

    juju = which('juju')
    if juju is None:
        juju = which('microk8s.juju')
    if juju is None:
        raise Exception("Juju not found!")

    if not url:
        status = yaml.safe_load(check_output([juju, 'status', '--format=yaml']))
        endpoint = status['applications']['istio-ingressgateway-operator']['address']
        try:
            ip_address(endpoint)
            endpoint += '.nip.io'
        except ValueError:
            pass
        url = f'http://{endpoint}/'

    if not password:
        output = check_output([juju, 'config', 'dex-auth', 'static-password'])
        password = output.decode('utf-8').strip()

    options = Options()
    if not headful:
        options.add_argument("--headless")

    profile = webdriver.FirefoxProfile()

    if proxy:
        profile.set_preference('network.proxy.type', 1)
        profile.set_preference('network.proxy.socks', proxy.split(':')[0])
        profile.set_preference('network.proxy.socks_port', int(proxy.split(':')[1]))

    kwargs = {
        'options': options,
        'seleniumwire_options': {'enable_har': True},
        'firefox_profile': profile,
    }

    with webdriver.Firefox(**kwargs) as driver:
        wait = WebDriverWait(driver, 180, 1, (JavascriptException,))
        # Go to URL and log in
        for _ in range(60):
            try:
                driver.get(url)
                break
            except WebDriverException:
                sleep(5)
        else:
            driver.get(url)
        driver.find_element_by_id("login").send_keys("admin")
        driver.find_element_by_id("password").send_keys(password)
        driver.find_element_by_tag_name("form").submit()

        # Ensure that main page loads properly
        script = fix_queryselector(['main-page', 'dashboard-view', '#Quick-Links'])
        wait.until(lambda x: x.execute_script(script))

        yield driver, wait, url

        Path(f'/tmp/selenium-{request.node.name}.har').write_text(driver.har)
        driver.get_screenshot_as_file(f'/tmp/selenium-{request.node.name}.png')


@pytest.mark.full
@pytest.mark.lite
def test_login(driver):
    driver, wait, url = driver
    driver.get(url)

    # Ensure that we're logged in properly
    script = fix_queryselector(['main-page', 'dashboard-view', '#Quick-Links'])
    wait.until(lambda x: x.execute_script(script))


@pytest.mark.full
@pytest.mark.lite
def test_notebook(driver):
    driver, wait, url = driver

    notebook_name = 'ci-test-' + ''.join(choices(ascii_lowercase, k=10))

    # Ensure that main page loads properly
    script = fix_queryselector(['main-page', 'dashboard-view', '#Quick-Links'])
    wait.until(lambda x: x.execute_script(script))

    # Navigate to Jupyter frontend
    script = fix_queryselector(['main-page', 'iframe-link[href=\'/jupyter/?ns=admin\'] .menu-item'])
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.click()')

    # Click "New Server" button
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('#newResource')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.click()')

    wait.until(EC.url_to_be(url + '_/jupyter/new?ns=admin'))

    # Enter server name
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('input[placeholder=\"Name\"]')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.value = "%s"' % notebook_name)
    driver.execute_script(script + '.dispatchEvent(new Event("input"))')

    # Click submit on the form. Sleep for 1 second before clicking the submit
    # button because shiny animations that ignore click events are simply a must.
    # Note that that was sarcasm. If you're reading this, please don't shit up
    # the web with braindead technologies.
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('form')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.dispatchEvent(new Event("ngSubmit"))')
    wait.until(EC.url_to_be(url + '_/jupyter/new?ns=admin'))

    # doc points at the nested Document hidden in all of the shadowroots
    # Saving as separate variable to make constructing `Document.evaluate`
    # query easier, as that requires `contextNode` to be equal to `doc`.
    doc = fix_queryselector(['main-page', 'iframe-container', 'iframe'])[7:]
    doc += ".contentWindow.document"

    # Since upstream doesn't use proper class names or IDs or anything, find the
    # <tr> containing elements that contain the notebook name and `ready`, signifying
    # that the notebook is finished booting up. Returns a reference to the containing
    # <tr> element. The result is a fairly unreadable XPath reference, but it works 🤷
    chonky_boi = '/'.join(
        [
            f"//*[contains(text(), '{notebook_name}')]",
            "ancestor::tr",
            "/*[contains(@class, 'ready')]",
            "ancestor::tr",
        ]
    )

    script = evaluate(doc, chonky_boi)
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(doc + '.querySelector(".action-button button").click()')

    # Make sure we can connect to a specific notebook's endpoint
    # Notebook is opened in a new tab, so we have to explicitly switch to it,
    # run our tests, close it, then switch back to the main window.
    driver.switch_to.window(driver.window_handles[-1])
    expected_path = f'/notebook/admin/{notebook_name}/lab'
    for _ in range(12):
        path = urlparse(driver.current_url).path
        if path == expected_path:
            break

        sleep(5)
        driver.refresh()
    else:
        pytest.fail(
            "Waited too long for selenium to open up notebook server. "
            f"Expected current path to be `{expected_path}`, got `{path}`."
        )

    # Wait for main content div to load
    # TODO: More testing of notebook UIs
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jp-Launcher-sectionTitle")))
    driver.execute_script('window.close()')
    driver.switch_to.window(driver.window_handles[-1])

    # Delete notebook, and wait for it to finalize
    driver.execute_script(evaluate(doc, "//*[contains(text(), 'delete')]") + '.click()')
    driver.execute_script(f"{doc}.body.querySelector('.mat-warn').click()")

    script = evaluate(doc, "//*[contains(text(), '{notebook_name}')]")
    wait.until_not(lambda x: x.execute_script(script))
