# (c) AlenPaulVarghese
# -*- coding: utf-8 -*-

import asyncio
import logging
from http.client import ResponseNotReady

from playwright.async_api import Browser, Error

from helper import read_driver_file
from helper.images import render_statics
from helper.printer import Printer, RenderType, ScrollMode

logger = logging.getLogger(__name__)


async def screenshot_engine(browser: Browser, printer: Printer, user_lock: asyncio.Event):
    page = await browser.new_page(viewport=printer.resolution)  # type: ignore
    try:
        await page.goto(url=printer.link, timeout=60000.0)
        driver_file = await read_driver_file()
        title, _ = await asyncio.gather(page.title(), page.evaluate(driver_file))
        printer.set_filename(title[:14])
        if printer.type == RenderType:
            height, width = await page.evaluate("[getHeight(), getWidth()]")
            page_data = {"Height": height, "Width": width}
            byteio_file = await render_statics(title[:25], page_data)
            printer.set_location(byteio_file)
        else:
            if printer.scroll_control != ScrollMode.OFF and printer.fullpage is True:
                if printer.scroll_control == ScrollMode.AUTO:
                    await page.evaluate("scroll(getHeight());")
                elif printer.scroll_control == ScrollMode.MANUAL:
                    asyncio.create_task(page.evaluate("progressiveScroll();"))
                    await user_lock.wait()
                    await page.evaluate("cancelScroll()")
            if printer.type == RenderType.PDF:
                await page.pdf(**printer.get_render_arguments(), path=printer.file)  # type: ignore
            else:
                await page.screenshot(**printer.get_render_arguments(), path=printer.file)  # type: ignore
    except Error as e:
        logger.error(msg=e, exc_info=True)
        raise e
    except asyncio.CancelledError as e:
        raise ResponseNotReady("server got interuppted, please try again later") from e
    finally:
        await page.close()
