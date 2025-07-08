import asyncio

async def scroll_to_bottom(page, step=200, delay=0.1, max_attempts=50):
    attempts = 0
    while attempts < max_attempts:
        reached_bottom = await page.evaluate('''(step) => {
            function getScrollableElement() {
                // Get all elements with scrollable overflow
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return (
                        (style.overflowY === 'auto' || style.overflowY === 'scroll') &&
                        el.scrollHeight > el.clientHeight
                    );
                });
                // Return the largest one, or document.scrollingElement as fallback
                if (elements.length === 0) return document.scrollingElement || document.documentElement;
                return elements.reduce((a, b) => (a.scrollHeight > b.scrollHeight ? a : b));
            }
            const el = getScrollableElement();
            const { scrollTop, scrollHeight, clientHeight } = el;
            if (scrollTop + clientHeight >= scrollHeight - 1) return true;
            el.scrollBy({ top: step, behavior: 'smooth' });
            return false;
        }''', step)
        if reached_bottom:
            break
        attempts += 1
        await asyncio.sleep(delay)
    # If the page is very short, just wait a bit
    if attempts == 0:
        await asyncio.sleep(2)
