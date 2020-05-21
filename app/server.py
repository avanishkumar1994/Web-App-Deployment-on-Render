import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

export_file_url = 'https://www.googleapis.com/drive/v3/files/1C2tcnsCcK87i8sgtHzoquJjapHxL2tYG?alt=media&key=AIzaSyBw2UXIZBrzGktNwFmSFqmZQsI08pj245I'
export_file_name = 'export.pkl'

classes = ['character_29_waw', 'character_6_cha', 'character_32_patalosaw', 'character_7_chha', 'character_4_gha', 'character_24_bha', 'character_12_thaa', 'character_22_pha', 'character_5_kna', 'character_10_yna', 'character_1_ka', 'character_27_ra', 'character_13_daa', 'digit_2', 'character_21_pa', 'digit_5', 'character_8_ja', 'digit_4', 'digit_3', 'character_3_ga', 'character_18_da', 'character_28_la', 'character_19_dha', 'character_23_ba', 'character_33_ha', 'character_2_kha', 'character_34_chhya', 'character_9_jha', 'character_11_taamatar', 'character_25_ma', 'character_30_motosaw', 'character_17_tha', 'character_35_tra', 'character_36_gya', 'character_31_petchiryakha', 'character_15_adna', 'character_14_dhaa', 'character_16_tabala', 'digit_6', 'digit_1', 'digit_8', 'character_20_na', 'character_26_yaw', 'digit_9', 'digit_0', 'digit_7']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    return JSONResponse({'result': str(prediction)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
