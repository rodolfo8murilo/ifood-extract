import asyncio
import subprocess
from time import sleep
from scrapy import signals
from scrapy.http import HtmlResponse
from playwright.async_api import async_playwright
from seleniumbase import sb_cdp


class SeleniumBaseCDPMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def __init__(self):
        self.sb = None

    async def process_request(self, request, spider):

        if not request.meta.get("selenium"):
            return None

        playwright = None
        browser = None

        try:
            spider.logger.info("Starting SeleniumBase CDP with hardware spoofing...")

            self.sb = await asyncio.to_thread(
                sb_cdp.Chrome,
                locale="en",
                headless=False,
                chromium_arg=[
                    "--window-size=1280,900",
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--enable-webgl",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            await asyncio.sleep(2)
            endpoint_url = self.sb.get_endpoint_url()

            playwright = await async_playwright().start()

            browser = await playwright.chromium.connect_over_cdp(endpoint_url)

            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            spider.logger.info(f"Accessing page via Xvfb: {request.url}")

            await page.goto(request.url, timeout=120000, wait_until="domcontentloaded")

            await page.wait_for_timeout(7000)

            spider.logger.info("Executing captcha bypass (solve_captcha)...")
            await asyncio.to_thread(self.sb.solve_captcha)
            spider.logger.info("Captcha command sent.")

            await page.wait_for_timeout(7000)

            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                spider.logger.info(
                    "Timeout waiting for 'networkidle', proceeding with current HTML."
                )

            if context.pages:
                page = context.pages[-1]

            spider.logger.info(f"URL successfully captured: {page.url}")
            html_content = await page.content()

            spider.logger.info("Closing browser instances safely...")

            try:
                await browser.disconnect()
                await playwright.stop()
            except Exception:
                pass

            try:
                await asyncio.to_thread(self.sb.driver.quit)
            except Exception:
                pass

            return HtmlResponse(
                url=request.url,
                body=html_content.encode("utf-8"),
                encoding="utf-8",
                request=request,
            )

        except Exception as e:
            spider.logger.error(
                f"Critical error in SeleniumBase CDP Middleware: {str(e)}"
            )

            try:
                if browser:
                    await browser.close()
            except Exception:
                pass
            try:
                if playwright:
                    await playwright.stop()
            except Exception:
                pass
            try:
                if self.sb:
                    await asyncio.to_thread(self.sb.driver.quit)
            except Exception:
                pass

            return None

    def spider_closed(self, spider):

        if hasattr(self, "sb") and self.sb:
            try:
                spider.logger.info("Terminating SeleniumBase driver gracefully...")
                self.sb.driver.quit()
                self.sb = None
            except Exception:
                pass

        sleep(0.5)

        try:
            spider.logger.info(
                "Executing preventive pkill for any remaining orphaned Chrome processes..."
            )
            subprocess.run(
                "pkill -9 -f chrome",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            spider.logger.error(f"Error executing pkill on system: {str(e)}")

        spider.logger.info("Process cleanup completed successfully!")
