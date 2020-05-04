import pytest
import json
from shlscraper.spiders.liiga import LiigaSpider


@pytest.fixture()
def spider():
    return LiigaSpider()


with open('json/liigaLeague.json') as f:
    data = json.load(f)
# print(data)


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        (
            "http://liiga.fi/fi/tilastot/2019-2020/runkosarja/joukkueet/",
            data
        )
    ],
)
def test_parse(spider, response, expected):
    result = next(spider.parse(response))
    print(data)
    print(result)
    assert result == expected, "Data json dump is wrong KeyValue Error"


print('=======================================')
print('\ttest case is passed')
print('=======================================')
