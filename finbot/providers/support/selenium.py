from functools import wraps


class DefaultBrowserFactory(object):
    def __init__(self, headless=True, developer_tools=False):
        self.headless = headless
        self.developer_tools = developer_tools

    def __call__(self):
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        if self.developer_tools:
            opts.add_argument("--auto-open-devtools-for-tabs")
        opts.headless = self.headless
        driver = Chrome(options=opts)
        return driver


def _safe_cond(cond):
    @wraps(cond)
    def impl(*args, **kwargs):
        try:
            return cond(*args, **kwargs)
        except Exception as e:
            return None
    return impl


class any_of(object):
    def __init__(self, *args):
        self.conds = [_safe_cond(cond) for cond in args]

    def __call__(self, driver):
        return any(cond(driver) for cond in self.conds)


class all_of(object):
    def __init__(self, *args):
        self.conds = [_safe_cond(cond) for cond in args]

    def __call__(self, driver):
        return all(cond(driver) for cond in self.conds)


class negate(object):
    def __init__(self, cond):
        self.cond = _safe_cond(cond)

    def __call__(self, driver):
        return not(self.cond(driver))


def get_cookies(browser):
    return {cookie["name"]: cookie["value"] for cookie in browser.get_cookies()}
