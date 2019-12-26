class DefaultBrowserFactory(object):
    def __init__(self, headless=True):
        self.headless = headless

    def __call__(self):
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        opts.headless = self.headless
        return Chrome(options=opts)


class any_of(object):
    def __init__(self, *args):
        self.conds = args

    def __call__(self, driver):
        return any(cond(driver) for cond in self.conds)


class all_of(object):
    def __init__(self, *args):
        self.conds = args

    def __call__(self, driver):
        return all(cond(driver) for cond in self.conds)


class negate(object):
    def __init__(self, cond):
        self.cond = cond

    def __call__(self, driver):
        return not(self.cond(driver))


def dump_html(block):
    return block.get_attribute("innerHTML")


def find_element_maybe(plural_handler, *args, **kwargs):
    elements = plural_handler(*args, **kwargs)
    if len(elements) < 1:
        return None
    return elements[0]


def get_cookies(browser):
    return {cookie["name"]: cookie["value"] for cookie in browser.get_cookies()}
