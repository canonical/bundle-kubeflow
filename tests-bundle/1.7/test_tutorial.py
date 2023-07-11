import time
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

TESTS_DIR = Path(__file__).resolve().parent


@pytest.mark.usefixtures("failed_check")
class TestGetStartedTutorial:
    """Test that covers 'get started tutorial'.

    Current test is based on the following tutorial:
    https://charmed-kubeflow.io/docs/get-started-with-charmed-kubeflow

    It will execute on the deployed kubeflow bundle and will create a notebook.
    Once notebook is created, it will be executed with an example code.
    For code see advanced_notebook.py.tmpl file.

    Once notebook is executed, we will check that all 5 Epochs are completed.

    Prerequisites for the test:
        - Full bundle is deployed
        - User namespace is created (in order to skip welcome page)
    """

    @pytest.mark.selenium
    def test_create_notebook(self, driver):
        # this test relies on the name ordering to be executed after deployment
        driver.get("http://10.64.140.43.nip.io")
        login_field = WebDriverWait(driver, 200).until(
            expected_conditions.presence_of_element_located(
                (
                    By.ID,
                    "login",
                )
            )
        )
        login_field.send_keys("admin")
        driver.find_element(by=By.ID, value="password").send_keys("admin")
        driver.find_element(by=By.ID, value="submit-login").click()
        shadow_root = driver.find_element(by=By.XPATH, value="/html/body/main-page").shadow_root
        sidepanel_menu = shadow_root.find_elements(by=By.CLASS_NAME, value="menu-item")
        for menu_item in sidepanel_menu:
            if menu_item.accessible_name == "Notebooks":
                menu_item.click()
                break
        else:
            raise Exception("Notebooks menu item not found")

        time.sleep(3)
        notebooks_content = shadow_root.find_element(by=By.ID, value="Content")
        notebooks_shadow_root = notebooks_content.find_element(
            by=By.XPATH, value="neon-animated-pages/neon-animatable[4]/iframe-container"
        ).shadow_root
        iframe = notebooks_shadow_root.find_element(by=By.ID, value="iframe")
        driver.switch_to.frame(iframe)
        print("switched to iframe")

        new_notebook_button = WebDriverWait(driver, 300).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    (
                        "/html/body/app-root/app-index/app-index-default/"
                        "div/lib-title-actions-toolbar/div/div[4]/div/button"
                    ),
                )
            )
        )
        new_notebook_button.click()
        notebook_name_input = WebDriverWait(driver, 300).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/app-root/app-form-new/div/div/form/app-form-name/"
                    "lib-form-section/div/lib-name-input/mat-form-field/div/div[1]/div[3]/input",
                )
            )
        )
        notebook_name_input.send_keys("test-notebook")
        custom_notebook_menu = driver.find_element(
            by=By.XPATH,
            value=(
                "/html/body/app-root/app-form-new/div/div/form/app-form-image/"
                "lib-form-section/div/div[2]/mat-accordion/mat-expansion-panel/mat-expansion-panel-header"
            ),
        )
        custom_notebook_menu.click()
        images_drop_down_menu = driver.find_element(
            by=By.XPATH,
            value=(
                "/html/body/app-root/app-form-new/div/div/form/app-form-image/"
                "lib-form-section/div/div[2]/mat-accordion/"
                "mat-expansion-panel/div/div/mat-form-field/div/div[1]/div[3]"
            ),
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

        launch_button = driver.find_element(
            by=By.XPATH, value="/html/body/app-root/app-form-new/div/div/div/div/button"
        )
        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable(launch_button))
        launch_button.click()
        time.sleep(3)  # wait for notebook to start

        app_root = driver.find_element(by=By.XPATH, value="/html/body/app-root")
        connect_button = app_root.find_element(
            by=By.XPATH,
            value="app-index/app-index-default/div/div/lib-table/table/tbody/tr/td[10]/div/lib-action-button/button",
        )
        WebDriverWait(driver, 400).until(
            expected_conditions.element_to_be_clickable(connect_button)
        )
        connect_button.click()

        # notebook page
        driver.switch_to.window(driver.window_handles[1])
        assert "http://10.64.140.43.nip.io/notebook/admin/test-notebook/lab" in driver.current_url

        time.sleep(2)
        new_kernel = WebDriverWait(driver, 60).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[1]/div[3]/div[2]/div[1]/div[3]/div[3]/div[3]/div/div/div[2]/div[2]/div",
                )
            )
        )
        new_kernel.click()

        text_field = driver.find_element(
            by=By.XPATH,
            value=(
                "/html/body/div[1]/div[3]/div[2]/div[1]/div[3]/div[3]/div[3]/"
                "div/div[3]/div[2]/div[2]/div/div[1]/textarea"
            ),
        )

        with open(TESTS_DIR / "advanced_notebook.py.tmpl") as f:
            text_field.send_keys(f.read())

        time.sleep(2)

        action = ActionChains(driver)
        action.key_down(Keys.CONTROL).key_down(Keys.ENTER).perform()

        # wait for the notebook to finish
        for i in range(60):
            output_field = WebDriverWait(driver, 600).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[1]/div[3]/div[2]/div[1]/div[3]/div[3]/"
                        "div[3]/div/div[5]/div[2]/div[4]/div[2]/pre",
                    )
                )
            )
            print(f"Waiting for notebook to finish, current output: {output_field.text}")
            if "Epoch 5" not in output_field.text:
                time.sleep(15)
            else:
                break
        else:
            raise Exception("Notebook did not finish in 600 seconds")
