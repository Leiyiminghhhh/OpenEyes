from crawl4ai import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, BrowserConfig, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from pydantic import BaseModel, Field


class MainPageCrawlerConfig:
    source: str
    type: str
    url: str

    def __repr__(self) -> str:
        return f"<MainPageCrawlerConfig: source={self.source}, type={self.type}, url={self.url}>"

    def __init__(self, source, type, url):
        self.source = source
        self.type = type
        self.url = url


class MainPageModelFee(BaseModel):
    url: str = Field(..., description="文章链接")
    title: str = Field(..., description="文章标题")


class MainPageCrawler:
    def __init__(self, config: MainPageCrawlerConfig):
        self.config = config

        extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 10000}
        llm_config = LLMConfig(provider="ollama/qwen3:8b",
                               base_url="http://localhost:11434")
        self.crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            page_timeout=80000,
            extraction_strategy=LLMExtractionStrategy(
                llm_config=llm_config,
                schema=MainPageModelFee.model_json_schema(),
                extraction_type="schema",
                instruction="""
                    读取文章内容，仔细筛选出新闻的链接，去除目录，中英文切换等导航链接，尽可能全面地收集信息，
                    并生成一个list，每个list的元素为json格式的摘要，格式如下：
                    {
                        "url": "文章链接",
                        "title": "文章标题",
                    }
                """,
                extra_args=extra_args,
            ),
            delay_before_return_html=5,
        )
        self.browser_config = BrowserConfig(headless=False)

    async def Run(self):
        async with AsyncWebCrawler(confg=self.browser_config) as crawler:
            results = await crawler.arun(url=self.config.url, config=self.crawler_config)
            return results.extracted_content
