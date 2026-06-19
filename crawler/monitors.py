import json
import os
from datetime import datetime
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.monitors.mixins.spider import SpiderMonitorMixin


@monitors.name("iFood Performance Validation")
class IfoodPerformanceMonitor(Monitor, SpiderMonitorMixin):
    def test_verificacao_geral_da_rodada(self):
        successes = self.data.stats.get("extracao/sucesso", 0)
        failures = self.data.stats.get("extracao/falha", 0)
        system_errors = self.data.stats.get("log_count/ERROR", 0)
        total_processed = successes + failures

        report = {
            "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spider_name": self.data.spider.name,
            "metrics": {
                "total_urls_processed": total_processed,
                "successes": successes,
                "failures_or_captchas": failures,
                "system_or_code_errors": system_errors,
            },
            "round_status": "SUCCESS",
        }

        try:
            if total_processed > 0:
                success_rate = (successes / total_processed) * 100
                if success_rate < 95.0:
                    report["round_status"] = "WARNING: Low success rate"

                    self.assertTrue(
                        success_rate >= 95.0,
                        msg=f"Expected 95% success rate. Achieved only {success_rate:.1f}% "
                        f"({successes} out of {total_processed}). iFood security might have increased!",
                    )
            else:
                report["round_status"] = "FAILURE: No items processed"
                self.assertGreater(
                    total_processed,
                    0,
                    msg="The spider closed without processing any URL!",
                )

        finally:
            os.makedirs("test_history", exist_ok=True)
            file_name = f"test_history/round_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False)

            print(f"\n[Spidermon] Round history saved to: {file_name}")


class SpiderCloseMonitorSuite(MonitorSuite):
    monitors = [
        IfoodPerformanceMonitor,
    ]
