# pylint: disable=too-few-public-methods
import logging
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SaveJsonPipeline:
    def open_spider(self, spider):
        self.filename = "products_output.json"
        self.file = open(self.filename, "w", encoding="utf-8")

        self.file.write("[\n")
        self.is_first_item = True

    def close_spider(self, spider):
        self.file.write("\n]")
        self.file.close()

    def process_item(self, item, spider):

        if isinstance(item, BaseModel):
            dict_data = item.model_dump()
        else:
            dict_data = dict(item)

        line = json.dumps(dict_data, ensure_ascii=False, indent=4)

        if not self.is_first_item:
            self.file.write(",\n")
        else:
            self.is_first_item = False

        indented_lines = "\n".join(f"    {l}" for l in line.split("\n"))
        self.file.write(indented_lines)

        return item
