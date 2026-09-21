import sys,asyncio,os
from playwright.async_api import async_playwright
html,out=sys.argv[1],sys.argv[2]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1350},device_scale_factor=1)
        await pg.goto('file://'+os.path.abspath(html)); await pg.wait_for_timeout(800)
        n=await pg.evaluate("document.querySelectorAll('section.slide').length")
        for i in range(n):
            el=(await pg.query_selector_all('section.slide'))[i]
            ov=await el.evaluate("""e=>{const r=e.getBoundingClientRect();let bad=[];e.querySelectorAll('.body *').forEach(x=>{const q=x.getBoundingClientRect();if(q.bottom>r.bottom-40&&q.height>0)bad.push(x.className||x.tagName)});const body=e.querySelector('.body');const ft=e.querySelector('.ft');return {over:body.scrollHeight>body.clientHeight+2, bodyH:body.scrollHeight, clientH:body.clientHeight, bad:bad.slice(0,3)}}""")
            if ov['over'] or ov['bad']: print(f"TAŞMA UYARISI slayt {i+1}: {ov}")
            await el.screenshot(path=f'{out}/slide-{i+1}.png')
        await b.close()
        from PIL import Image
        ims=[Image.open(f'{out}/slide-{i+1}.png').resize((360,450)) for i in range(n)]
        cols=3; rows=(n+cols-1)//cols
        c=Image.new('RGB',(cols*360,rows*450),'white')
        for i,im in enumerate(ims): c.paste(im,((i%cols)*360,(i//cols)*450))
        c.save(f'{out}/contact.jpg',quality=85); print('OK',n,'slayt')
asyncio.run(main())
