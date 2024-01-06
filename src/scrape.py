import time
import random
from typing import Dict, List, Tuple, Union

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class InvalidYelpPage(Exception):
    """Invalid Yelp Page Returned."""

    def __str__(self):
        return "Recieved and invalid Yelp Page."


class DriverSetupFailed(Exception):
    """Driver Setup Failed."""

    def __str__(self):
        return "Failed to setup driver correctly."


def is_valid_yelp_page(page_source):
    """Check for a unique element, text, or structure specific to Yelp pages."""
    return "Yelp" in page_source and "Write a Review" in page_source


def setup_driver(proxy) -> webdriver:
    try:
        # Setup chrome options for headleess mode
        chrome_options = Options()

        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--proxy-server={proxy}")

        # Set up the WebDriver
        driver = webdriver.Chrome(
            options=chrome_options
        )  # Replace with your browser's driver
        return driver
    except Exception as e:  # pylint: disable=broad-except
        if isinstance(e, KeyboardInterrupt):
            raise e
        raise DriverSetupFailed from e


def parse_review_items(review_html: List[str]) -> Dict[str, str]:
    """Extract the name and content from the businesses reviews."""

    reviews = []
    for html in review_html:
        soup = BeautifulSoup(html, "html.parser")
        link_tags = soup.find_all("a")
        if len(link_tags) < 2:
            continue
        name = link_tags[1].text

        content_tags = soup.find_all("p")
        content = " ".join([p.text for p in content_tags])
        reviews.append({name.replace(".", ""): content})

    return reviews


def do_random_activity(driver: webdriver):
    """Take random actions to prevent getting caught by the Yelp police."""
    try:
        # Get all links on the page
        all_links = driver.find_elements(By.TAG_NAME, "a")
        time.sleep(
            random.uniform(0.5, 1.5)
        )  # Random sleep time between 1 and 3 seconds

        # Scroll to the chosen link
        choice = random.choice(all_links)
        driver.execute_script("arguments[0].scrollIntoView();", choice)

        # Click the link
        time.sleep(random.uniform(0.25, 0.5))
        choice.click()
        time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:  # pylint: disable=W0718
        if isinstance(e, KeyboardInterrupt):
            raise e
        return


def scrape_business_reviews(
    url, proxy
) -> Tuple[Union[Dict[str, str], None], Union[Exception, None]]:
    """Scrape the description of the Yelp business at the given URL."""

    try:
        driver = setup_driver(proxy)

        # Get the page and ensure it is valid (10 second timeout)
        driver.set_page_load_timeout(10)
        driver.get(url)

        if not is_valid_yelp_page(driver.page_source):
            raise InvalidYelpPage()

        # Wait for the specific 'Read More' button to be clickable, and click it
        reccomended_reviews = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "//section[@aria-label='Recommended Reviews']")
            )
        )

        # Get all headings on the page
        headings = driver.find_elements(By.TAG_NAME, "h3")
        random_heading = random.choice(headings)

        # Scroll to the random heading
        driver.execute_script("arguments[0].scrollIntoView();", random_heading)

        # Get every <li> element inside of reccomended_reviews
        review_items = reccomended_reviews.find_elements(By.TAG_NAME, "li")
        review_html = [item.get_attribute("innerHTML") for item in review_items]

        # Do some random stuff to avoid getting blocked by Yelp
        do_random_activity(driver)

        # Process each review item as needed
        reviews = parse_review_items(review_html)
        return reviews, None

    except TimeoutException as e:
        return None, e
    except DriverSetupFailed as e:
        print(f"Driver setup failed with proxy: {proxy}")
        return None, e
    except InvalidYelpPage as e:
        return None, e
    except Exception as e:  # pylint: disable=broad-except
        if isinstance(e, KeyboardInterrupt):
            raise e
        print(f"Error scraping page: {url}\n{e}")
        return None, e
    finally:
        driver.quit()


def scrape_business_page_content(
    url, proxy
) -> Tuple[Union[Dict[str, str], None], Union[Exception, None]]:
    """Scrape the description of the Yelp business at the given URL."""

    try:
        driver = setup_driver(proxy)

        # Get the page and ensure it is valid (10 second timeout)
        driver.set_page_load_timeout(10)
        driver.get(url)

        if not is_valid_yelp_page(driver.page_source):
            raise InvalidYelpPage()

        # Scrape all the text on the page into one long concatenated string
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Do some random stuff to avoid getting blocked by Yelp
        do_random_activity(driver)

        return page_text, None

    except TimeoutException as e:
        return None, e
    except DriverSetupFailed as e:
        print(f"Driver setup failed with proxy: {proxy}")
        return None, e
    except InvalidYelpPage as e:
        return None, e
    except Exception as e:  # pylint: disable=broad-except
        if isinstance(e, KeyboardInterrupt):
            raise e
        print(f"Error scraping page: {url}\n{e}")
        return None, e
    finally:
        driver.quit()
