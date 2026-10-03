from fastapi import FastAPI, Response

import qrcode
from io import BytesIO

app = FastAPI()


@app.get("/qr")
async def generate_qr(text: str):
    # QRコード生成
    img = qrcode.make(text)

    # PNG をメモリに書き出し
    buf = BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # PNG を返す
    return Response(content=png_bytes, media_type="image/png")
