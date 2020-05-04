import pytest
import json
from shlscraper.spiders.khl import KhlSpider


@pytest.fixture()
def spider():
    return KhlSpider()


with open('json/khlLeague.json') as f:
    data = json.load(f)
# print(data)


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        (
            "https://en.khl.ru/stat/teams/",
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
