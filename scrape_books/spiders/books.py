import re
from typing import Generator

import scrapy
from scrapy.http import Response


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = 0
        self.limit = 1000
        self.rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5,
        }

    def parse(
            self,
            response: Response,
            *args,
            **kwargs
    ) -> Generator[scrapy.Request, None, None] | None:
        if self.count > self.limit:
            return

        next_page = response.css("li.next > a::attr(href)").get()

        for book in response.css(".product_pod"):
            book_url = book.css("h3 > a::attr(href)").get()
            yield response.follow(book_url, callback=self.parse_book)
        if next_page:
            yield response.follow(next_page)

    def parse_book(
            self,
            response: Response,
            *args,
            **kwargs
    ) -> Generator[scrapy.Request, None, None]:
        title = response.css(".product_main > h1::text").get()
        description = response.xpath(
            '//div[@class="sub-header"]/following-sibling::p[1]/text()'
        ).get()

        price_text = response.css(".product_main > .price_color::text").get()
        price = float(price_text.replace("£", "")) if price_text else "N/A"

        rating_text = response.css(".star-rating::attr(class)").get()
        rating = self.rating_map.get(
            rating_text.split()[-1]
        ) if rating_text else "N/A"

        links = response.css(".breadcrumb > li")
        category = links[-2].css("a::text").get() if links else "N/A"

        table = response.css(".table.table.table-striped > tr")
        if table:
            upc = table[0].css("td::text").get()
            stock_text = table[5].css("td::text").get()
            stock = int(
                re.search(r"\((\d+)", stock_text).group(1)
            ) if stock_text else "N/A"
        else:
            upc = "N/A"
            stock = "N/A"

        self.count += 1
        yield {
            "title": title,
            "price": price,
            "amount_in_stock": stock,
            "rating": rating,
            "category": category,
            "description": description,
            "upc": upc,
        }
