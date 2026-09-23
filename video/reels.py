import sys, asyncio, os, subprocess, shutil
from playwright.async_api import async_playwright

html = sys.argv[1]
out = sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else 'video'   # 'video' | 'check'
FPS = 30

async def main():
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        await pg.goto('file://' + os.path.abspath(html))
        await pg.wait_for_timeout(1200)
        total = await pg.evaluate("window.TOTAL")
        el = await pg.query_selector('#stage')

        if mode == 'check':
            # one representative frame per scene + overflow report
            scenes = await pg.evaluate("[...document.querySelectorAll('.scene')].map(s=>[+s.dataset.in,+s.dataset.out])")
            for i, (a, z) in enumerate(scenes):
                t = z - 0.5
                await pg.evaluate(f"window.render({t})")
                await pg.wait_for_timeout(60)
                await el.screenshot(path=f'{out}/scene-{i+1}.png')
                ov = await pg.evaluate("""(()=>{const s=[...document.querySelectorAll('.scene')].find(x=>x.style.display!=='none');
                  const inn=s.querySelector('.inner');const r=inn.getBoundingClientRect();
                  let bad=[];inn.querySelectorAll('*').forEach(x=>{const q=x.getBoundingClientRect();
                  if(q.height>0&&(q.bottom>r.bottom+2||q.top<r.top-2||q.right>1080-80))bad.push((x.className||x.tagName)+'')});
                  return {over: inn.scrollHeight>inn.clientHeight+2, h:inn.scrollHeight, c:inn.clientHeight, bad:bad.slice(0,4)}})()""")
                if ov['over'] or ov['bad']:
                    print(f"TASMA UYARISI sahne {i+1}: {ov}")
            from PIL import Image
            n = len(scenes)
            ims = [Image.open(f'{out}/scene-{i+1}.png').resize((270, 480)) for i in range(n)]
            cols = 3; rows = (n + cols - 1) // cols
            c = Image.new('RGB', (cols*270, rows*480), 'white')
            for i, im in enumerate(ims): c.paste(im, ((i % cols)*270, (i//cols)*480))
            c.save(f'{out}/contact.jpg', quality=88)
            print('CHECK OK', n, 'sahne')
            await b.close(); return

        fr = f'{out}/frames'
        shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
        n = int(total * FPS)
        for i in range(n):
            await pg.evaluate(f"window.render({i/FPS})")
            await el.screenshot(path=f'{fr}/f-{i:04d}.jpg', type='jpeg', quality=92)
        # cover frame at 3.6s
        await pg.evaluate("window.render(3.6)")
        await el.screenshot(path=f'{out}/cover.jpg', type='jpeg', quality=92)
        await b.close()
        print('FRAMES', n)
        subprocess.run(['ffmpeg','-y','-framerate',str(FPS),'-i',f'{fr}/f-%04d.jpg',
            '-f','lavfi','-i','anullsrc=channel_layout=stereo:sample_rate=44100','-shortest',
            '-c:v','libx264','-profile:v','high','-level','4.1','-pix_fmt','yuv420p',
            '-crf','20','-preset','medium','-c:a','aac','-b:a','128k','-movflags','+faststart',
            f'{out}/reel.mp4'], check=True, capture_output=True)
        shutil.rmtree(fr, ignore_errors=True)
        print('OK', f'{out}/reel.mp4')

asyncio.run(main())
