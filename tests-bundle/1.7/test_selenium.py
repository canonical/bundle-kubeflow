import pytest
from selenium.webdriver.common.by import By


class TestGetStartedTutorial:
    @pytest.mark.selenium
    def test_selenium(self, driver):
        driver.get("https://quay.io/")
        msg = driver.find_element(by=By.XPATH, value="/html/body/div[1]/nav/span/div/div[1]/div[2]/ul[3]/li[4]/a")
        assert msg.text.lower() == "sign in"
