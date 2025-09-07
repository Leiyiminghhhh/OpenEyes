import asyncio
from crawl4ai import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, BrowserConfig, CacheMode, DefaultMarkdownGenerator
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from pydantic import BaseModel, Field

DEBUG = False

class RecordCrawlerConfig:
    urls: list

    def __init__(self, urls):
        self.urls = urls


class RecordModelFee(BaseModel):
    content: str = Field(..., description="文章内容摘要（300~500字）")
    tags: str = Field(..., description="把文章打个标签")
    time: str = Field(..., description="发布时间，格式为yyyy-MM-dd")
    title: str = Field(..., description="文章标题")


class RecordCrawler:
    def __init__(self, config: RecordCrawlerConfig):
        self.config = config
        extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 10000}
        llm_config = LLMConfig(provider="ollama/qwen3:8b",
                               base_url="http://localhost:11434")
        markdown_generator = DefaultMarkdownGenerator(content_source="fit_html")
        self.crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            page_timeout=80000,
            extraction_strategy=LLMExtractionStrategy(
                llm_config=llm_config,
                schema=RecordModelFee.model_json_schema(),
                extraction_type="schema",
                instruction="""
                    从文章中抽取内容，生成一个json格式的摘要，格式如下：
                    {
                        "content": "文章内容摘要（300~500字）",
                        "tags": "把文章打个标签",
                        "time": "发布时间，格式为yyyy-MM-dd",
                        "title": "文章标题"
                    }
                """,
                extra_args=extra_args,
            ),
            delay_before_return_html=5,
            mean_delay=0.5,
            max_range=1.5,
            simulate_user=True,
            scan_full_page=True,
            max_scroll_steps=5,
            only_text=True,
            word_count_threshold=200,
            log_console=True,
            markdown_generator=markdown_generator
        )
        self.browser_config = BrowserConfig(headless=True)

    async def __get_one_page(self, url):
        async with AsyncWebCrawler(confg=self.browser_config) as crawler:
            results = await crawler.arun(
                url=url,
                config=self.crawler_config)
            return results

    def Run(self):
        results = {}
        for url in self.config.urls:
            r = asyncio.run(self.__get_one_page(url))
            results[url] = r.extracted_content
            if DEBUG:
                # save html 
                html = r.html
                with open("test.html", "w", encoding="utf-8") as f:
                    f.write(html)
                with open("test.md", "w", encoding="utf-8") as f:
                    f.write(r.markdown)
                print(f"save html to test.html")
                print("url: ", url)
                print(f"result.extracted_content: {r.extracted_content}")
                print(f"result.redirected_url: {r.redirected_url}")
                # print(f"result.markdown: {r.markdown}")
        return results


def test():
    DEBUG = True
    url = "https://finance.eastmoney.com/a/202509053505213687.html"
    # url = "https://www.bbc.com/zhongwen/articles/c74098n2xy0o/simp"
    # url = "https://www.zaobao.com.sg/realtime/china/story20250906-7470442"
    # url = "https://openai.com/api/pricing/"
    RecordCrawler(RecordCrawlerConfig([url])).Run()


if __name__ == "__main__":
    test()