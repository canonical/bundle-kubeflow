def pytest_addoption(parser):
    parser.addoption("--proxy", action="store", help="Proxy to use")
    parser.addoption("--url", action="store", help="Juju controller")
    parser.addoption("--password", action="store", help="Juju model")
    parser.addoption("--headful", action="store_true", help="Juju model")
