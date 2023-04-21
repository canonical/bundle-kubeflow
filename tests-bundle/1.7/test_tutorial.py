import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class TestGetStartedTutorial:
    @pytest.mark.deploy
    def test_create_notebook(self, driver):
        # this test relies on the name ordering to be executed after deployment
        driver.get("http://10.64.140.43.nip.io")
        driver.find_element(by=By.ID, value="login").send_keys("admin")
        driver.find_element(by=By.ID, value="password").send_keys("admin")
        driver.find_element(by=By.ID, value="submit-login").click()
        shadow_root = driver.find_element(by=By.XPATH, value="/html/body/main-page").shadow_root
        sidepanel_menu = shadow_root.find_elements(by=By.CLASS_NAME, value="menu-item")
        for menu_item in sidepanel_menu:
            if menu_item.text == "Notebooks":
                menu_item.click()
                break

        notebooks_content = shadow_root.find_element(by=By.ID, value="Content")
        notebooks_shadow_root = notebooks_content.find_element(
            by=By.XPATH, value="neon-animated-pages/neon-animatable[4]/iframe-container"
        ).shadow_root
        iframe = notebooks_shadow_root.find_element(by=By.ID, value="iframe")
        driver.switch_to.frame(iframe)

        app_root = driver.find_element(by=By.XPATH, value="/html/body/app-root")
        new_notebook_button = app_root.find_element(
            by=By.XPATH,
            value="app-index/app-index-default/div/lib-title-actions-toolbar/div/div[4]/div/button",
        )
        new_notebook_button.click()
        app_root.find_element(
            by=By.XPATH,
            value="app-form-new/div/div/form/app-form-name/lib-form-section/div/lib-name-input/mat-form-field/div/div[1]/div[3]/input",
        ).send_keys("test-notebook")
        custom_notebook_menu = app_root.find_element(
            by=By.XPATH,
            value="app-form-new/div/div/form/app-form-image/lib-form-section/div/div[2]/mat-accordion/mat-expansion-panel/mat-expansion-panel-header",
        )
        custom_notebook_menu.click()
        images_drop_down_menu = app_root.find_element(
            by=By.XPATH,
            value="app-form-new/div/div/form/app-form-image/lib-form-section/div/div[2]/mat-accordion/mat-expansion-panel/div/div/mat-form-field/div/div[1]/div[3]",
        )
        images_drop_down_menu.click()
        all_notebook_images = driver.find_elements(by=By.CLASS_NAME, value="mat-option-text")

        assert all_notebook_images, "No notebook images found"

        for notebook_image in all_notebook_images:
            WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable(notebook_image)
            )
            if "jupyter-tensorflow-full" in notebook_image.text:
                print(f"Notebook found: {notebook_image.text}")
                notebook_image.click()
                break
        else:
            raise Exception("jupyter-tensorflow-full image not found")

        launch_button = app_root.find_element(
            by=By.XPATH, value="app-form-new/div/div/div/div/button"
        )
        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable(launch_button))
        launch_button.click()
        time.sleep(3)  # wait for notebook to start

        app_root = driver.find_element(by=By.XPATH, value="/html/body/app-root")
        connect_button = app_root.find_element(
            by=By.XPATH,
            value="app-index/app-index-default/div/div/lib-table/table/tbody/tr/td[10]/div/lib-action-button/button",
        )
        WebDriverWait(driver, 300).until(
            expected_conditions.element_to_be_clickable(connect_button)
        )
        connect_button.click()

        # notebook page
        driver.switch_to.window(driver.window_handles[1])
        assert "http://10.64.140.43.nip.io/notebook/admin/test-notebook/lab" in driver.current_url
