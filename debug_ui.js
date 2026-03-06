const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  try {
      const page = await browser.newPage();
      
      // Navigate to site
      await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
      
      // Fill the input
      await page.type('#market-url', 'https://polymarket.com/ru/event/texas-republican-senate-primary-winner');
      
      // Submit the form
      await page.click('#submit-btn');
      
      // Provide time for the fetch to error out
      await new Promise(r => setTimeout(r, 4000));
      
      // Check visibility of error-container
      const isVisible = await page.$eval('#error-container', el => {
          const style = window.getComputedStyle(el);
          return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
      });
      console.log("Is Error container visibly rendered on screen?", isVisible);
      
      // Take a screenshot
      await page.screenshot({ path: '/root/.gemini/antigravity/brain/248ab1a2-f2ac-496a-b4de-6eb925fa1ada/error_screenshot.png' });
      console.log("Saved an error screenshot.");

  } finally {
      await browser.close();
  }
})();
