from crawl4ai import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, BrowserConfig, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from pydantic import BaseModel, Field

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
        )
        self.browser_config = BrowserConfig(headless=True)

    async def Run(self):
        async with AsyncWebCrawler(confg=self.browser_config) as crawler:
            results = await crawler.arun_many(
                urls=self.config.urls,
                config=self.crawler_config)
            
            return {result.url:result.extracted_content for result in results}
