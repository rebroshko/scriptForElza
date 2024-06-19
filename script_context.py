from asyncio import sleep

from playwright.async_api import async_playwright


async def go_to_start_page(page):
    await page.goto("https://unu.im/tasks/orders")
    await sleep(1)


async def get_main_api(p):
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()
    return browser, page


async def get_context():
    async with async_playwright() as p:
        browser, page = await get_main_api(p)
        await go_to_start_page(page)
        await page.locator("//*[@name = 'email']").fill("otzivimega@gmail.com")
        await page.locator("//*[@name = 'password']").fill("FPQCBk")
        await sleep(15)
        await page.context.storage_state(path='context.json')
