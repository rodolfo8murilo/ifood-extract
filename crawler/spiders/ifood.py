import asyncio
from time import time
from scrapy import Spider, Request, signals
from pandas import read_csv
from crawler.items import IFoodItemModel


class IfoodSpider(Spider):
    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            "crawler.pipelines.SaveJsonPipeline": 1000,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "crawler.middlewares.SeleniumBaseCDPMiddleware": 900,
        },
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_TIMEOUT": 120,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 5.0,
        "AUTOTHROTTLE_MAX_DELAY": 60.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "AUTOTHROTTLE_DEBUG": False,
        "DOWNLOAD_DELAY": 3.0,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [403, 429, 500, 502, 503, 504],
        "RETRY_PRIORITY_ADJUST": -1,
    }

    name = "ifood"
    allowed_domains = ["www.ifood.com.br"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        csv_path = "ifood_urls_padrao_item_1000.csv"
        df = read_csv(csv_path)

        self.start_urls = df["url"].tolist()
        self.start_time = time()
        self.initial_total_urls = len(self.start_urls)

        self.logger.info(f"Total URLs loaded: {self.initial_total_urls}")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(IfoodSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    async def start(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta={"selenium": True},
            )
            await asyncio.sleep(5)

    def parse(self, response):
        self.logger.info("Processing rendered page data.")
        title = response.css("div.product-detail__description::text").get()

        if title is None:
            yield from self.parse_error(response.url)
            return

        image = response.css("div.product-detail__image-container img::attr(src)").get()
        price = response.css("div.product-card__price::text").get()
        if price:
            normal_price = price.strip()
            discount_price = None
        else:
            normal_price = response.css(
                "span.product-card__price--original::text"
            ).get()
            discount_price = response.css(
                "span.product-card__price--discount::text"
            ).get()

        self.crawler.stats.inc_value("extracao/sucesso")

        item_data = IFoodItemModel(
            title=str(title) if title else "",
            url=str(response.url),
            image=str(image) if image else None,
            normal_price=str(normal_price) if normal_price else None,
            discount_price=str(discount_price) if discount_price else None,
            status="success",
            error=None,
        )

        yield item_data

    def _build_error_item(self, url: str) -> IFoodItemModel:

        self.crawler.stats.inc_value("extracao/falha")

        return IFoodItemModel(
            title="",
            url=str(url),
            image=None,
            normal_price=None,
            discount_price=None,
            status="error",
            error="Produto indisponível ou pagina não carregada",
        )

    def parse_error(self, url):
        yield self._build_error_item(url)

    def handle_error(self, failure):
        yield self._build_error_item(failure.request.url)

    def spider_closed(self, spider):
        successes = self.crawler.stats.get_value("extracao/sucesso", 0)
        failures = self.crawler.stats.get_value("extracao/falha", 0)
        total_processed = successes + failures

        if total_processed > 0:
            success_rate = (successes / total_processed) * 100
        else:
            success_rate = 0.0

        total_time_minutes = int((time() - self.start_time) / 60)

        self.logger.info("-" * 50)
        self.logger.info(f"Total de URLs processadas: {total_processed}")
        self.logger.info(f"Sucessos: {successes}")
        self.logger.info(f"Falhas: {failures}")
        self.logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        self.logger.info(f"Tempo total de execução: {total_time_minutes} minuto(s)")
        self.logger.info("-" * 50)
