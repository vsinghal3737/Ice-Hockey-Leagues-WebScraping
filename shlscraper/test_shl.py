import pytest
import json
from shlscraper.spiders.shl import ShlSpider


@pytest.fixture()
def spider():
    return ShlSpider()


with open('json/shlLeague.json') as f:
    data = json.load(f)
# print(data)


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        (
            "https://www.shl.se/statistik/",
            data
        )
    ],
)
def test_parse(spider, response, expected):
    result = next(spider.parse(response))
    assert result == expected, "Data json dump is wrong KeyValue Error"


print('=======================================')
print('\ttest case is passed')
print('=======================================')
