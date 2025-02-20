import time
import asyncio
from typing import List
from tqdm import tqdm
from playwright.async_api import async_playwright


def generate_urls() -> List[str]:
    prefixes = ['KFC', 'subway', 'Subway', 'Wingstop', 'BK', 'MC', 'Timezone', 'popolamama', 'optmelawai', ]
    return [
        f'https://s.id/{prefix}{date:02d}{month:02d}'
        for prefix in prefixes
        for date in range(1, 32)
        for month in range(1, 13)
    ]


async def scrape(browser, url, file):
    try:
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=10000)  # 10-second timeout
        if page.url.startswith('https://kuponku.id/'):
            print(f'{url}, {page.url}', file=file, flush=True)
        await context.close()
    except Exception as e:
        tqdm.write(f'Error scraping {url}: {e}')


async def worker(queue, browser, pbar, file):
    while not queue.empty():
        url = await queue.get()
        await scrape(browser, url, file)
        queue.task_done()
        pbar.update(1)


async def main(num_workers=10, filename=None):
    filename = filename or f'generated/{int(time.time())}.txt'
    urls = generate_urls()

    with tqdm(total=len(urls), desc=filename) as pbar, open(filename, 'a+') as file:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            queue = asyncio.Queue()

            for url in urls:
                await queue.put(url)

            tasks = [asyncio.create_task(worker(queue, browser, pbar, file)) for _ in range(num_workers)]
            await queue.join()  # Wait for all tasks to complete

            await browser.close()

    print(f'Finished scraping. Results saved to {filename}')


if __name__ == '__main__':
    asyncio.run(main())
