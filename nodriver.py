import nodriver as uc

async def main():

    browser = await uc.start()
    # page = await browser.get('https://www.realestate.com.au/')
    page = await browser.get('https://www.zillow.com/')
    input("")



if __name__ == '__main__':
    # since asyncio.run never worked (for me)
    uc.loop().run_until_complete(main())
