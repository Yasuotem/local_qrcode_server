## 概要




## 全体の流れ

1. **PowerShell で自己署名証明書を作る（CurrentUser）**
2. **その証明書を .pfx として書き出す**
3. **Git Bash + OpenSSL で .pfx → .key / .pem に変換する**
4. **証明書を「信頼されたルート証明機関」に登録する**
5. **FastAPI(Uvicorn) を HTTPS で起動する**
6. **Excel の `IMAGE()` から HTTPS で叩く**


---

## 1. PowerShellで自己署名証明書を作る（CurrentUser）

### 目的
- Windows の「自分のユーザーの証明書ストア」に  
  `localhost` 用の自己署名証明書を作る。

### コマンド

PowerShell（普通に起動でOK）で：

```powershell
New-SelfSignedCertificate `
  -DnsName "localhost" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -FriendlyName "LocalhostDevCert"
```

### うまくいったときに起こること
- エラーが出ずに、証明書オブジェクトが返る
- `certmgr.msc` を開いて  
  「個人 → 証明書」に `LocalhostDevCert` が増えている

### 確認方法

```powershell
Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.FriendlyName -eq "LocalhostDevCert" }
```

これで1件出てくればOK。

---

## 2. 証明書を .pfx として書き出す

### 目的
- Windows の証明書ストアにある証明書を  
  **秘密鍵付きのファイル（.pfx）**として取り出す。

### コマンド

```powershell
$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.FriendlyName -eq "LocalhostDevCert" }

Export-PfxCertificate `
  -Cert $cert `
  -FilePath "$env:USERPROFILE\localhost.pfx" `
  -Password (ConvertTo-SecureString -String "password" -Force -AsPlainText)
```

### うまくいったときに起こること
- エラーなしで終了
- エクスプローラーで `C:\Users\<あなたのユーザー名>\localhost.pfx` が存在する

---

## 3. Git Bash + OpenSSLで .pfx → .key / .pem に変換

### 目的
- FastAPI(Uvicorn) が読める形式（**秘密鍵 .key と証明書 .pem**）に変換する。

### 前提
- Git for Windows が入っている（Git Bash が使える）
- Git Bash で `openssl version` が通る

### 手順

Git Bash を開いて：

```bash
cd ~
ls localhost.pfx
```

ここで `localhost.pfx` が見えていればOK。

#### 秘密鍵を取り出す（.key）

```bash
openssl pkcs12 -in localhost.pfx -nocerts -out localhost.key -nodes -password pass:password
```

- パスフレーズを聞かれたら `password` と入力
- 終了後、`ls` すると `localhost.key` ができている

#### 証明書を取り出す（.pem）

```bash
openssl pkcs12 -in localhost.pfx -clcerts -nokeys -out localhost.pem -password pass:password
```

- 同じく `password` を入力
- 終了後、`localhost.pem` ができている

### うまくいったときに起こること
- `~/localhost.key` と `~/localhost.pem` が存在する
- 中身はテキスト（`-----BEGIN PRIVATE KEY-----` / `-----BEGIN CERTIFICATE-----`）

### OpenSSLが固まる場合は以下のやり方で実行する
```bash
openssl pkcs12 -in localhost.pfx -clcerts -nokeys \
  -out localhost.pem \
  -passin pass:password \
  -passout pass:password
```

---

## 4. 証明書を「信頼されたルート証明機関」に登録する

### 目的
- Excel が「この HTTPS は信頼できる」と判断するようにする。

### 手順

1. `Win + R` → `certmgr.msc` → Enter
2. 左ペインで「個人 → 証明書」を開く
3. `LocalhostDevCert` を探す（発行先が `localhost`）
4. 右クリック → コピー
5. 左ペインで「信頼されたルート証明機関 → 証明書」を開く
6. 右クリック → 貼り付け

### うまくいったときに起こること
- 「信頼されたルート証明機関 → 証明書」にも `LocalhostDevCert` が現れる
- これで Excel やブラウザが `https://localhost` を「安全」とみなす

---

## 5. FastAPI(Uvicorn) を HTTPS で起動する

### 目的
- `https://127.0.0.1:8000` で FastAPI が待ち受けるようにする。

### コマンド例

プロジェクトディレクトリで：

```bash
python -m uvicorn main:app \
  --host localhost \
  --port 8000 \
  --ssl-keyfile ~/localhost.key \
  --ssl-certfile ~/localhost.pem
```

※ `main:app` はあなたの FastAPI のエントリに合わせて調整。

### うまくいったときに起こること
- コンソールに `Uvicorn running on https://localhost:8000` と出る
- ブラウザで `https://localhost:8000/qr?text=hello` を開くと  
  → セキュリティ警告なしで PNG が表示される（か、ダウンロードされる）

---

## 6. Excel の IMAGE関数から叩く

### 目的
- Excel のセルから HTTPS API を呼び出して、QR PNG を表示する。

### 例

```excel
=IMAGE("https://localhost:8000/qr?text=" & A2)
```

- `A2` に文字列が入っていると、その内容の QR が表示される
- 固定なら：

```excel
=IMAGE("https://localhost:8000/qr?text=https://example.com")
```

### うまくいったときに起こること
- セルに QR 画像が表示される
- エラー「source 引数の URL は https プロトコルを使用する必要があります」は出ない

### Uvicornがctrl+cで終了しない場合

#### タスクマネージャーでPythonを強制終了する

1. Ctrl + Shift + Esc

2. 詳細タブ

3. Python.exe または uvicorn.exe を探す

4. 右クリック → 終了

---

## よく詰まりそうなポイントと対処

### **New-SelfSignedCertificate でまたエラーが出る場合**
- `Cert:\CurrentUser\My` を使っているか確認（`LocalMachine` ではない）
- PowerShell を「管理者」で一度試すのもあり

### **Git Bash から localhost.pfx が見えない場合**
- PowerShell で `echo $env:USERPROFILE` を確認  
- Git Bash で `cd /c/Users/あなたのユーザー名` してから `ls`

### **ブラウザで HTTPS に警告が出る場合**
- `certmgr.msc` で「信頼されたルート証明機関」に `LocalhostDevCert` が入っているか確認

---

もしどこかのステップで  
「このコマンドを打ったらこういうメッセージが出た」  
というのがあれば、そのまま貼ってくれれば、そこだけピンポイントで一緒にほどいていこう。