from playwright.sync_api import Page, expect, sync_playwright

def verify_seo(page: Page):
    page.goto("http://127.0.0.1:8000/")

    # Check Title
    expect(page).to_have_title("Project Store | The Maker's Hub: DIY Kits, Components & Code Snippets")

    # Check Meta Description
    description = page.locator('meta[name="description"]')
    expect(description).to_have_attribute("content", "Pakistan's ultimate store for Students & Hobbyists. Shop ESP32 modules, sensors, ready-to-use DIY Project Kits, and professional Software Projects/Code Snippets.")

    # Check OG Title
    og_title = page.locator('meta[property="og:title"]')
    expect(og_title).to_have_attribute("content", "Project Store | The Maker's Hub")

    # Check JSON-LD
    schema = page.locator('script[type="application/ld+json"]').first
    expect(schema).to_be_attached()

    # Screenshot
    page.screenshot(path="verification/seo_verification.png")
    print("SEO verification passed!")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_seo(page)
        finally:
            browser.close()
