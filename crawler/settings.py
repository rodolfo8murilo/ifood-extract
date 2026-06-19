SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ADDONS = {}


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

ROBOTSTXT_OBEY = False


CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

EXTENSIONS = {
    "spidermon.contrib.scrapy.extensions.Spidermon": 500,
}

SPIDERMON_ENABLED = True

SPIDERMON_SPIDER_CLOSE_MONITORS = ("crawler.monitors.SpiderCloseMonitorSuite",)

SPIDERMON_SPIDER_CLOSE_ACTIONS = ("spidermon.contrib.actions.LogActions",)
