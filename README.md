# QRCodeLocalServer

ローカルにAPIサーバーとして常駐させ、ExcelのIMAGE関数から利用してQRコードを表示させることを目的としたアプリケーションです。

## インストール

```bash
git clone https://github.com/Yasuotem/local_qrcode_server.git
cd local_qrcode_server
pip install -r requirements.txt
```

```bash
python -m uvicorn main:app \
  --host localhost \
  --port 8000 \
  --ssl-keyfile ~/localhost.key \
  --ssl-certfile ~/localhost.pem
```
