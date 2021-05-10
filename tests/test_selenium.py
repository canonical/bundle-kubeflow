from ipaddress import ip_address
from random import choices
from shutil import which
from string import ascii_lowercase
from subprocess import check_output
from time import sleep

import pytest
import yaml
from selenium import webdriver
from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import presence_of_element_located, url_to_be
from selenium.webdriver.support.ui import WebDriverWait


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
        endpoint = status['applications']['istio-ingressgateway']['address']
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

    with webdriver.Firefox(options=options, firefox_profile=profile) as driver:
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
    driver.get(url)

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
    script += ".contentWindow.document.body.querySelector('#add-nb')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.click()')

    # Enter server name
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('#mat-input-0')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.value = "%s"' % notebook_name)
    driver.execute_script(script + '.dispatchEvent(new Event("input"))')

    # Open the image dropdown menu
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('#mat-select-5')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.click()')

    # Select an image
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('#mat-option-12')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.click()')

    # Submit form
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    script += ".contentWindow.document.body.querySelector('form')"
    wait.until(lambda x: x.execute_script(script))
    driver.execute_script(script + '.dispatchEvent(new Event("ngSubmit"))')

    # Wait for notebook to spin up
    script = fix_queryselector(['main-page', 'iframe-container', 'iframe'])
    row_script = (
        'return [...' + script[7:] + ".contentWindow.document.body.querySelectorAll('.mat-row')]"
    )
    row_exists = row_script + (".find(div => div.innerHTML.includes('%s'))" % notebook_name)
    row_ready = row_script + (
        ".find(div => div.querySelector('.running') && div.innerHTML.includes('%s'))"
        % notebook_name
    )
    wait.until(lambda x: x.execute_script(row_ready))

    # Open notebook
    driver.execute_script(row_exists + ".querySelector('button.mat-accent').click()")

    # Make sure we can connect to a specific notebook's endpoint
    # Notebook is opened in a new tab, so we have to explicitly switch to it,
    # run our tests, close it, then switch back to the main window.
    driver.switch_to.window(driver.window_handles[-1])
    expected_url = url + 'notebook/admin/%s/tree?' % notebook_name
    for _ in range(60):
        current_url = driver.current_url
        print("CURRENT URL: %s" % current_url)
        if current_url == expected_url:
            break
        else:
            sleep(5)
            driver.refresh()
    else:
        pytest.abort("Waited too long for selenium to open up notebook server!")

    wait.until(url_to_be(url + 'notebook/admin/%s/tree?' % notebook_name))
    wait.until(presence_of_element_located((By.ID, "new-dropdown-button")))
    driver.execute_script('window.close()')
    driver.switch_to.window(driver.window_handles[-1])

    # Delete notebook
    driver.execute_script(row_exists + ".querySelector('button:last-child').click()")
    driver.execute_script(script + ".contentWindow.document.body.querySelector('.yes').click()")
    long_wait = WebDriverWait(driver, 600, 1, (JavascriptException,))
    long_wait.until_not(lambda x: x.execute_script(row_exists))
