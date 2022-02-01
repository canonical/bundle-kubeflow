def pytest_addoption(parser):
    parser.addoption("--proxy", action="store", help="Proxy to use")
    parser.addoption("--url", action="store", help="Juju controller")
    parser.addoption("--username", action="store", help="Dex username (email address)")
    parser.addoption("--password", action="store", help="Dex password")
    parser.addoption("--headful", action="store_true", help="Juju model")
