def pytest_addoption(parser):
    parser.addoption("--proxy", action="store", help="Proxy to use")
    parser.addoption("--url", action="store", help="Kubeflow dashboard URL")
    parser.addoption(
        "--username",
        action="store",
        help="Dex username (email address)",
        default="user123@email.com"
    )
    parser.addoption("--password", action="store", help="Dex password", default="user123")
    parser.addoption("--headful", action="store_true", help="Juju model")
