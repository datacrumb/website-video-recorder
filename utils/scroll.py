import asyncio

async def scroll_to_bottom(page, total_duration=28, step=200):
    """
    Smoothly scrolls to the bottom of the page over total_duration seconds.
    If the bottom is reached early, waits at the bottom for the remaining time.
    """
    start = asyncio.get_event_loop().time()
    elapsed = 0
    interval = 0.5  # seconds between scrolls
    while elapsed < total_duration:
        reached_bottom = await page.evaluate('''(step) => {
            function getScrollableElement() {
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return (
                        (style.overflowY === 'auto' || style.overflowY === 'scroll') &&
                        el.scrollHeight > el.clientHeight
                    );
                });
                if (elements.length === 0) return document.scrollingElement || document.documentElement;
                return elements.reduce((a, b) => (a.scrollHeight > b.scrollHeight ? a : b));
            }
            const el = getScrollableElement();
            const { scrollTop, scrollHeight, clientHeight } = el;
            if (scrollTop + clientHeight >= scrollHeight - 1) return true;
            el.scrollBy({ top: step, behavior: 'smooth' });
            return false;
        }''', step)
        await asyncio.sleep(interval)
        elapsed = asyncio.get_event_loop().time() - start
        if reached_bottom:
            # Wait at the bottom for the rest of the duration
            remaining = total_duration - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)
            break
    print(f"Scroll completed in {elapsed:.2f} seconds (including wait at bottom if any)")
