## 4. OAuth 2.0 実装

### 認可コードフロー

```python
from urllib.parse import urlencode
import secrets

class OAuth2Client:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        redirect_uri: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
    
    def get_authorization_url(self, scopes: list[str], state: str = None) -> str:
        """認可URLを生成"""
        state = state or secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }
        
        return f"{self.authorize_url}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> TokenResponse:
        """認可コードをトークンに交換"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return TokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in"),
                token_type=data.get("token_type", "Bearer")
            )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """トークンをリフレッシュ"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            response.raise_for_status()
            return TokenResponse(**response.json())
```

### トークン管理

```python
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, oauth_client: OAuth2Client, storage: TokenStorage):
        self.oauth = oauth_client
        self.storage = storage
    
    async def get_valid_token(self, user_id: str) -> str:
        """有効なアクセストークンを取得（必要に応じてリフレッシュ）"""
        token_data = await self.storage.get(user_id)
        
        if not token_data:
            raise TokenNotFoundError()
        
        # 有効期限チェック（5分の余裕を持つ）
        if token_data.expires_at > datetime.now() + timedelta(minutes=5):
            return token_data.access_token
        
        # リフレッシュ
        new_token = await self.oauth.refresh_token(token_data.refresh_token)
        
        await self.storage.save(user_id, new_token)
        
        return new_token.access_token
```

---

## 5. Webhook実装

### Webhook受信

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

WEBHOOK_SECRET = "your-webhook-secret"

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """署名検証"""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    event = json.loads(payload)
    
    # イベント処理
    match event["type"]:
        case "payment_intent.succeeded":
            await handle_payment_success(event["data"]["object"])
        case "payment_intent.failed":
            await handle_payment_failure(event["data"]["object"])
        case _:
            pass  # 未対応イベントは無視
    
    return {"status": "ok"}
```

### Webhook送信

```python
import hashlib
import hmac
import httpx
from datetime import datetime

class WebhookSender:
    def __init__(self, secret: str):
        self.secret = secret
    
    def _generate_signature(self, payload: str, timestamp: str) -> str:
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"
    
    async def send(self, url: str, event: dict, max_retries: int = 3) -> bool:
        payload = json.dumps(event)
        timestamp = str(int(datetime.now().timestamp()))
        signature = self._generate_signature(payload, timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": timestamp,
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        content=payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        return True
                    
                    # リトライ対象外のエラー
                    if response.status_code in (400, 401, 404):
                        return False
                        
            except httpx.TimeoutException:
                pass
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
        
        return False
```

---

## 6. エラーハンドリング

### エラー分類

```python
class ExternalAPIError(Exception):
    """外部APIエラーの基底クラス"""
    pass

class RateLimitError(ExternalAPIError):
    """レート制限エラー"""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after

class AuthenticationError(ExternalAPIError):
    """認証エラー"""
    pass

class ServiceUnavailableError(ExternalAPIError):
    """サービス利用不可"""
    pass

class InvalidRequestError(ExternalAPIError):
    """リクエスト不正"""
    pass
```

### エラーハンドリング

```python
async def call_api_with_handling(client: APIClient, path: str):
    try:
        return await client.get(path)
    
    except RateLimitError as e:
        # レート制限: 待機してリトライ or キューに入れる
        logger.warning(f"Rate limited, retry after {e.retry_after}s")
        await asyncio.sleep(e.retry_after or 60)
        return await client.get(path)
    
    except AuthenticationError:
        # 認証エラー: トークン更新
        await refresh_credentials()
        return await client.get(path)
    
    except ServiceUnavailableError:
        # サービス障害: フォールバック
        return get_cached_data(path)
    
    except InvalidRequestError as e:
        # リクエスト不正: ログして上位に伝播
        logger.error(f"Invalid request: {e}")
        raise
```

---

