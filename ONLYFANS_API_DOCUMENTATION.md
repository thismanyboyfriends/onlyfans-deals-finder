# OnlyFans API Documentation

**Base URL:** `https://onlyfans.com/api2/v2`

**Version:** v2

This documentation is reverse-engineered from the OF-Scraper repository and describes the OnlyFans API endpoints used for accessing user profiles, subscriptions, posts, messages, and pricing information.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request Signing](#request-signing)
3. [Common Headers](#common-headers)
4. [Rate Limiting & Error Handling](#rate-limiting--error-handling)
5. [Endpoints](#endpoints)
   - [User & Profile](#user--profile)
   - [Subscriptions](#subscriptions)
   - [Posts & Timeline](#posts--timeline)
   - [Messages](#messages)
   - [Purchased Content](#purchased-content)
   - [Stories & Highlights](#stories--highlights)
   - [Labels](#labels)
   - [Lists](#lists)
6. [Data Models](#data-models)
7. [Finding Deals](#finding-deals)

---

## Authentication

OnlyFans API requires authentication via cookies and custom headers. You need to extract these from your browser session.

### Required Authentication Data

Store in `auth.json`:

```json
{
  "auth_id": "your_user_id",
  "sess": "your_session_cookie",
  "auth_uid": "your_auth_uid",
  "user_agent": "your_browser_user_agent",
  "x-bc": "generated_token"
}
```

### Generating `x-bc` Token

The `x-bc` token is generated using:

```
timestamp_ms = current_time_in_milliseconds
random1 = random_number(0, 1e12)
random2 = random_number(0, 1e12)
user_agent = your_user_agent

parts = [timestamp_ms, random1, random2, user_agent]
msg = base64(parts[0]) + "." + base64(parts[1]) + "." + base64(parts[2]) + "." + base64(parts[3])
x-bc = SHA1(msg)
```

---

## Request Signing

**Critical:** All authenticated API requests must be cryptographically signed.

### Signing Process

1. Fetch dynamic signing rules from external sources (datawhores, digitalcriminals, xagler, rafa, etc.)
2. Extract signing parameters:
   - `static_param`: Static string from signing rule
   - `format`: Format string for final signature
   - `checksum_indexes`: Array of indexes for checksum calculation
   - `checksum_constant`: Constant value for checksum

3. Create signature:

```python
timestamp = current_time_in_milliseconds()
path = url_path_with_query_string
user_id = auth_id

message = "\n".join([static_param, timestamp, path, user_id])
sha1_hash = SHA1(message)

# Calculate checksum
checksum = sum(sha1_hash[i] for i in checksum_indexes) + checksum_constant

# Format final signature
final_signature = format.format(sha1_hash, abs(checksum))
```

4. Add to headers:
   - `sign`: final_signature
   - `time`: timestamp

### Example Dynamic Rule Sources

- **Datawhores:** (URL in environment config)
- **DigitalCriminals:** (URL in environment config)
- **Xagler:** (URL in environment config)
- **Rafa:** (URL in environment config)

Rules are cached for 30 minutes and refreshed automatically.

---

## Common Headers

### Authenticated Requests

```http
accept: application/json, text/plain, */*
app-token: 33d57ade8c02dbc5a333db99ff9ae26a
user-id: {auth_id}
x-bc: {generated_token}
referer: https://onlyfans.com
user-agent: {your_user_agent}
sign: {computed_signature}
time: {timestamp_ms}
cookie: auth_id={auth_id}; sess={sess}; auth_uid_={auth_uid}
```

### Anonymous Requests

```http
accept: application/json, text/plain, */*
app-token: 33d57ade8c02dbc5a333db99ff9ae26a
x-bc: {generated_token}
referer: https://onlyfans.com
user-id: 0
user-agent: {anonymous_user_agent}
```

---

## Rate Limiting & Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 401 | Unauthorized | Refresh auth credentials & signing rules |
| 403 | Forbidden | Refresh signing rules, wait and retry |
| 404 | Not Found | User deleted or doesn't exist |
| 429 | Too Many Requests | Exponential backoff (wait 1-60 seconds) |

### Recommended Settings

- **Max concurrent connections:** 12
- **Retry attempts:** 3-10 (depending on endpoint)
- **Min retry wait:** 1 second
- **Max retry wait:** 60 seconds
- **Cache profile data:** 30 minutes
- **Pagination limit:** 10-100 items per request

---

## Endpoints

### User & Profile

#### Get Current User Info

```http
GET /users/me
```

**Response 200:**

```json
{
  "id": 123456,
  "username": "username",
  "name": "Display Name",
  "email": "email@example.com",
  "isAuth": true,
  "balance": 0,
  ...
}
```

#### Get User Profile

```http
GET /users/{username_or_id}
```

**Parameters:**
- `{username_or_id}` - Username string or numeric user ID

**Response 200:**

```json
{
  "id": 123456,
  "username": "modelname",
  "name": "Model Display Name",
  "about": "Bio text",
  "avatar": "https://...",
  "header": "https://...",
  "joinDate": "2020-01-01T00:00:00+00:00",
  "subscribePrice": 9.99,
  "currentSubscribePrice": 4.99,
  "isRealPerformer": true,
  "isRestricted": false,
  "lastSeen": "2024-01-01T12:00:00+00:00",
  "postsCount": 500,
  "photosCount": 300,
  "videosCount": 200,
  "audiosCount": 10,
  "archivedPostsCount": 50,
  "subscribedByData": {
    "subscribeAt": "2023-01-01T00:00:00+00:00",
    "expiredAt": "2024-02-01T00:00:00+00:00",
    "renewedAt": "2024-01-01T00:00:00+00:00",
    "regularPrice": 9.99,
    "status": "Active",
    "subscribes": [
      {
        "startDate": "2023-01-01T00:00:00+00:00",
        "duration": 30,
        "price": 9.99
      }
    ]
  },
  "subscribedByExpireDate": "2024-02-01T00:00:00+00:00",
  "promotions": [
    {
      "id": 12345,
      "price": 3.99,
      "duration": 30,
      "canClaim": true,
      "title": "Limited offer!",
      "endsAt": "2024-01-31T00:00:00+00:00"
    }
  ]
}
```

**Response 404:** User not found or deleted

```json
{
  "username": "deleted_model_placeholder"
}
```

---

### Subscriptions

#### Get Subscription Count

```http
GET /subscriptions/count/all
```

**Response 200:**

```json
{
  "subscriptions": {
    "active": 25,
    "expired": 10
  }
}
```

#### Get Active Subscriptions

```http
GET /subscriptions/subscribes?offset={offset}&limit=10&type=active&format=infinite
```

**Parameters:**
- `offset` (integer, default: 0) - Pagination offset
- `limit` (integer, default: 10, max: 10) - Results per page
- `type` (string) - "active", "expired", or "all"
- `format` (string, default: "infinite") - Response format

**Response 200:**

```json
{
  "list": [
    {
      "id": 123456,
      "username": "modelname",
      "name": "Model Name",
      "avatar": "https://...",
      "header": "https://...",
      "subscribePrice": 9.99,
      "currentSubscribePrice": 4.99,
      "subscribedByData": {
        "subscribeAt": "2023-01-01T00:00:00+00:00",
        "expiredAt": "2024-02-01T00:00:00+00:00",
        "renewedAt": "2024-01-01T00:00:00+00:00",
        "regularPrice": 9.99,
        "status": "Active"
      },
      "promotions": [
        {
          "id": 12345,
          "price": 3.99,
          "canClaim": true
        }
      ],
      "isRestricted": false,
      "lastSeen": "2024-01-01T12:00:00+00:00"
    }
  ],
  "hasMore": true
}
```

#### Get Expired Subscriptions

```http
GET /subscriptions/subscribes?offset={offset}&limit=10&type=expired&format=infinite
```

**Parameters:** Same as active subscriptions

**Response:** Same structure as active subscriptions

---

### Posts & Timeline

#### Get Timeline Posts

```http
GET /users/{user_id}/posts?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&pinned=0&format=infinite
```

**Parameters:**
- `{user_id}` (integer) - User ID
- `limit` (integer, default: 100) - Results per page
- `order` (string) - "publish_date_asc" or "publish_date_desc"
- `skip_users` (string, default: "all") - Skip user data in response
- `skip_users_dups` (integer, default: 1) - Skip duplicate user data
- `pinned` (integer, default: 0) - Include pinned posts (0 or 1)
- `format` (string, default: "infinite") - Response format

**Response 200:**

```json
{
  "list": [
    {
      "id": 987654321,
      "postedAt": "2024-01-01T12:00:00+00:00",
      "postedAtPrecise": "1704110400.123",
      "createdAt": "2024-01-01T12:00:00+00:00",
      "text": "Post text content",
      "price": 0,
      "isArchived": false,
      "canPurchase": false,
      "media": [
        {
          "id": 111222333,
          "type": "photo",
          "url": "https://...",
          "preview": "https://...",
          "canView": true,
          "hasError": false
        }
      ],
      "mediaCount": 1,
      "isMediaReady": true,
      "commentsCount": 5,
      "favoritesCount": 10,
      "tipsAmount": 0
    }
  ],
  "hasMore": true
}
```

#### Get Next Timeline Page

```http
GET /users/{user_id}/posts?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&afterPublishTime={timestamp}&pinned=0&format=infinite
```

**Parameters:**
- `afterPublishTime` (string) - Precise timestamp from last post's `postedAtPrecise`

#### Get Pinned Posts

```http
GET /users/{user_id}/posts?skip_users=all&pinned=1&counters={counters}&format=infinite
```

#### Get Individual Post

```http
GET /posts/{post_id}?skip_users=all
```

**Parameters:**
- `{post_id}` (integer) - Post ID

#### Get Archived Posts

```http
GET /users/{user_id}/posts/archived?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&format=infinite
```

#### Get Streams

```http
GET /users/{user_id}/posts/streams?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&format=infinite
```

---

### Messages

#### Get Messages

```http
GET /chats/{chat_id}/messages?limit=100&order=desc&skip_users=all&skip_users_dups=1
```

**Parameters:**
- `{chat_id}` (integer) - Chat/user ID
- `limit` (integer, default: 100) - Results per page
- `order` (string, default: "desc") - "asc" or "desc"

**Response 200:**

```json
{
  "list": [
    {
      "id": 123456789,
      "fromUser": {
        "id": 111222,
        "username": "modelname"
      },
      "text": "Message text",
      "createdAt": "2024-01-01T12:00:00+00:00",
      "postedAt": "2024-01-01T12:00:00+00:00",
      "price": 0,
      "isOpened": true,
      "isNew": false,
      "canPurchase": false,
      "media": [
        {
          "id": 999888777,
          "type": "photo",
          "url": "https://...",
          "preview": "https://...",
          "canView": true
        }
      ]
    }
  ],
  "hasMore": true
}
```

#### Get Next Messages Page

```http
GET /chats/{chat_id}/messages?limit=100&id={last_message_id}&order=desc&skip_users=all&skip_users_dups=1
```

**Parameters:**
- `id` (integer) - Last message ID from previous page

#### Get Specific Messages

```http
GET /chats/{chat_id}/messages?limit=10&order=desc&skip_users=all&firstId={message_id}
```

**Parameters:**
- `firstId` (integer) - Specific message ID to retrieve

---

### Purchased Content

#### Get Purchased Content (Single User)

```http
GET /posts/paid?limit=100&skip_users=all&format=infinite&offset={offset}&user_id={user_id}
```

**Parameters:**
- `offset` (integer, default: 0) - Pagination offset
- `user_id` (integer) - Filter by specific user

**Response 200:**

```json
{
  "list": [
    {
      "id": 555666777,
      "fromUser": {
        "id": 123456,
        "username": "modelname"
      },
      "text": "Purchased post text",
      "createdAt": "2024-01-01T12:00:00+00:00",
      "price": 15.00,
      "isOpened": true,
      "media": [
        {
          "id": 888999000,
          "type": "video",
          "url": "https://...",
          "canView": true
        }
      ]
    }
  ],
  "hasMore": true
}
```

#### Get All Purchased Content

```http
GET /posts/paid?limit=100&skip_users=all&format=infinite&offset={offset}
```

**Parameters:**
- `offset` (integer, default: 0) - Pagination offset

---

### Stories & Highlights

#### Get Highlights with Stories

```http
GET /users/{user_id}/stories/highlights?limit=5&offset={offset}&unf=1
```

**Parameters:**
- `{user_id}` (integer) - User ID
- `limit` (integer, default: 5) - Results per page
- `offset` (integer, default: 0) - Pagination offset
- `unf` (integer, default: 1) - Include unfinished stories

#### Get Single Story

```http
GET /users/{user_id}/stories?unf=1
```

#### Get Specific Highlight Story

```http
GET /stories/highlights/{story_id}?unf=1
```

**Parameters:**
- `{story_id}` (integer) - Story/highlight ID

#### Get Specific Story

```http
GET /stories/{story_id}
```

---

### Labels

#### Get User Labels

```http
GET /users/{user_id}/labels?limit=100&offset={offset}&order=desc&non-empty=1
```

**Parameters:**
- `{user_id}` (integer) - User ID
- `limit` (integer, default: 100) - Results per page
- `offset` (integer, default: 0) - Pagination offset
- `order` (string, default: "desc") - Sort order
- `non-empty` (integer, default: 1) - Only return non-empty labels

**Response 200:**

```json
{
  "list": [
    {
      "id": 11223344,
      "name": "Favorites",
      "count": 25
    }
  ],
  "hasMore": false
}
```

#### Get Posts by Label

```http
GET /users/{user_id}/posts?limit=100&offset={offset}&order=publish_date_desc&skip_users=all&counters=0&format=infinite&label={label_id}
```

**Parameters:**
- `label` (integer) - Label ID to filter by

---

### Lists

#### Get User Lists

```http
GET /lists?offset={offset}&skip_users=all&limit=100&format=infinite
```

**Parameters:**
- `offset` (integer, default: 0) - Pagination offset

**Response 200:**

```json
{
  "list": [
    {
      "id": 55667788,
      "name": "My Custom List",
      "usersCount": 10
    }
  ],
  "hasMore": false
}
```

#### Get Users in List

```http
GET /lists/{list_id}/users?offset={offset}&limit=100&format=infinite
```

**Parameters:**
- `{list_id}` (integer) - List ID
- `offset` (integer, default: 0) - Pagination offset

**Response 200:**

```json
{
  "list": [
    {
      "id": 123456,
      "username": "modelname",
      "name": "Model Name",
      "avatar": "https://..."
    }
  ],
  "hasMore": false
}
```

---

## Data Models

### User/Subscription Object

```typescript
{
  id: number
  username: string
  name: string
  about: string | null
  avatar: string | null
  header: string | null
  joinDate: string (ISO 8601)
  subscribePrice: number
  currentSubscribePrice: number
  isRealPerformer: boolean
  isRestricted: boolean
  lastSeen: string (ISO 8601) | null
  postsCount: number
  photosCount: number
  videosCount: number
  audiosCount: number
  archivedPostsCount: number
  subscribedByData: {
    subscribeAt: string (ISO 8601)
    expiredAt: string (ISO 8601) | null
    renewedAt: string (ISO 8601) | null
    regularPrice: number
    status: "Active" | "Set to Expire" | "Expired"
    subscribes: Array<{
      startDate: string (ISO 8601)
      duration: number
      price: number
    }>
  } | null
  subscribedByExpireDate: string (ISO 8601) | null
  promotions: Array<{
    id: number
    price: number
    duration: number
    canClaim: boolean
    title: string
    endsAt: string (ISO 8601)
  }> | null
}
```

### Post Object

```typescript
{
  id: number
  postedAt: string (ISO 8601)
  postedAtPrecise: string (decimal timestamp)
  createdAt: string (ISO 8601)
  text: string | null
  price: number
  isArchived: boolean
  canPurchase: boolean
  media: Array<MediaObject>
  mediaCount: number
  isMediaReady: boolean
  commentsCount: number
  favoritesCount: number
  tipsAmount: number
  fromUser?: {
    id: number
    username: string
  }
}
```

### Media Object

```typescript
{
  id: number
  type: "photo" | "video" | "audio" | "gif"
  url: string
  preview: string | null
  thumb: string | null
  canView: boolean
  hasError: boolean
  locked: boolean | null
  duration: number | null (for videos/audio)
  videoSources: {
    [quality: string]: string
  } | null
}
```

### Message Object

```typescript
{
  id: number
  fromUser: {
    id: number
    username: string
    name: string
  }
  text: string | null
  createdAt: string (ISO 8601)
  postedAt: string (ISO 8601)
  price: number
  isOpened: boolean
  isNew: boolean
  canPurchase: boolean
  media: Array<MediaObject>
}
```

---

## Finding Deals

### Pricing Fields Explained

When analyzing subscription/profile data for deals, focus on these fields:

1. **`subscribePrice`** - Regular subscription price (full price)
2. **`currentSubscribePrice`** - Current price to subscribe (may be discounted)
3. **`subscribedByData.regularPrice`** - Regular price for already subscribed users
4. **`promotions[]`** - Array of promotional offers

### Promotion Object

```typescript
{
  id: number
  price: number           // Discounted price
  duration: number        // Days of subscription
  canClaim: boolean       // Whether you can claim this promo
  title: string
  endsAt: string         // When promo expires
}
```

### Finding the Best Deal

To find the lowest available price:

```python
def get_best_price(user_data):
    # Filter claimable promotions
    claimable_promos = [p for p in user_data.get('promotions', []) if p['canClaim']]

    # Sort by price
    claimable_promos.sort(key=lambda x: x['price'])

    # Compare prices
    current_price = user_data.get('currentSubscribePrice')
    regular_price = user_data.get('subscribePrice')
    lowest_promo = claimable_promos[0]['price'] if claimable_promos else None

    # Return lowest available
    prices = [p for p in [current_price, lowest_promo, regular_price] if p is not None]
    return min(prices) if prices else 0
```

### Identifying Deal Scenarios

1. **New Subscription Deal:**
   - `currentSubscribePrice < subscribePrice` indicates a discount

2. **Promotional Deal:**
   - Check `promotions` array where `canClaim: true`
   - Sort by `price` to find lowest

3. **Renewal Deal:**
   - For already subscribed users, compare `subscribedByData.regularPrice` with available promotions

4. **Expiring Soon:**
   - Check `subscribedByData.expiredAt` to find subscriptions expiring soon
   - These may offer renewal deals

### Example Deal Detection

```python
def find_deals(subscriptions):
    deals = []

    for user in subscriptions:
        regular_price = user.get('subscribePrice', 0)
        current_price = user.get('currentSubscribePrice', 0)

        # Check for discount on current price
        if current_price > 0 and current_price < regular_price:
            discount_pct = ((regular_price - current_price) / regular_price) * 100
            deals.append({
                'username': user['username'],
                'regular_price': regular_price,
                'current_price': current_price,
                'discount_percent': discount_pct,
                'type': 'current_discount'
            })

        # Check for claimable promotions
        claimable_promos = [p for p in user.get('promotions', [])
                           if p.get('canClaim')]

        if claimable_promos:
            best_promo = min(claimable_promos, key=lambda x: x['price'])
            if best_promo['price'] < regular_price:
                discount_pct = ((regular_price - best_promo['price']) / regular_price) * 100
                deals.append({
                    'username': user['username'],
                    'regular_price': regular_price,
                    'promo_price': best_promo['price'],
                    'discount_percent': discount_pct,
                    'duration': best_promo.get('duration'),
                    'ends_at': best_promo.get('endsAt'),
                    'type': 'promotional_deal'
                })

    # Sort by discount percentage
    deals.sort(key=lambda x: x['discount_percent'], reverse=True)
    return deals
```

### Monitoring Subscription Status

```python
from datetime import datetime, timedelta

def check_expiring_subscriptions(subscriptions, days_threshold=7):
    expiring = []
    now = datetime.now()
    threshold = now + timedelta(days=days_threshold)

    for user in subscriptions:
        subscribed_data = user.get('subscribedByData')
        if not subscribed_data:
            continue

        expired_at = subscribed_data.get('expiredAt')
        if expired_at:
            expiry_date = datetime.fromisoformat(expired_at.replace('Z', '+00:00'))

            if now < expiry_date < threshold:
                # Check for renewal deals
                promotions = user.get('promotions', [])
                claimable = [p for p in promotions if p.get('canClaim')]

                expiring.append({
                    'username': user['username'],
                    'expires_at': expired_at,
                    'days_remaining': (expiry_date - now).days,
                    'regular_price': subscribed_data.get('regularPrice'),
                    'renewal_deals': claimable
                })

    return expiring
```

---

## Best Practices

### 1. Caching
- Cache profile data for 30 minutes to reduce API calls
- Cache signing rules for 30 minutes
- Store subscription lists locally to detect price changes

### 2. Rate Limiting
- Use connection pooling (max 12 concurrent)
- Implement exponential backoff on 429 errors
- Add random jitter to retry delays

### 3. Error Handling
- Refresh auth credentials on 401 errors
- Refresh signing rules on 403 errors
- Log all errors for debugging

### 4. Pagination
- Always check `hasMore` field in responses
- Use appropriate offsets for pagination
- Handle empty result sets gracefully

### 5. Deal Monitoring
- Poll subscriptions endpoint every 1-4 hours
- Compare current prices with cached prices
- Send notifications when significant discounts appear
- Track promo expiration dates

---

## Example Implementation

### Python Example: Get All Active Subscriptions with Deals

```python
import requests
import time
from typing import List, Dict

class OnlyFansAPI:
    def __init__(self, auth_id: str, sess: str, user_agent: str, x_bc: str):
        self.base_url = "https://onlyfans.com/api2/v2"
        self.auth_id = auth_id
        self.sess = sess
        self.user_agent = user_agent
        self.x_bc = x_bc

    def _get_headers(self, path: str) -> Dict[str, str]:
        """Generate headers with signature"""
        timestamp = str(int(time.time() * 1000))

        # Get signing rules (implement your signing logic)
        sign = self._create_signature(path, timestamp)

        return {
            'accept': 'application/json, text/plain, */*',
            'app-token': '33d57ade8c02dbc5a333db99ff9ae26a',
            'user-id': self.auth_id,
            'x-bc': self.x_bc,
            'referer': 'https://onlyfans.com',
            'user-agent': self.user_agent,
            'sign': sign,
            'time': timestamp,
            'cookie': f'auth_id={self.auth_id}; sess={self.sess}'
        }

    def _create_signature(self, path: str, timestamp: str) -> str:
        """Implement signature creation logic"""
        # Fetch dynamic rules and create signature
        # See "Request Signing" section for implementation
        pass

    def get_active_subscriptions(self) -> List[Dict]:
        """Get all active subscriptions"""
        all_subs = []
        offset = 0
        has_more = True

        while has_more:
            path = f'/subscriptions/subscribes?offset={offset}&limit=10&type=active&format=infinite'
            url = self.base_url + path
            headers = self._get_headers(path)

            response = requests.get(url, headers=headers)

            if response.status_code == 429:
                time.sleep(30)  # Rate limited, wait and retry
                continue

            data = response.json()
            all_subs.extend(data.get('list', []))

            has_more = data.get('hasMore', False)
            offset += 10

        return all_subs

    def find_deals(self) -> List[Dict]:
        """Find best deals from active subscriptions"""
        subscriptions = self.get_active_subscriptions()
        deals = []

        for user in subscriptions:
            regular = user.get('subscribePrice', 0)
            current = user.get('currentSubscribePrice', 0)

            # Current discount
            if 0 < current < regular:
                deals.append({
                    'username': user['username'],
                    'type': 'current_discount',
                    'regular_price': regular,
                    'sale_price': current,
                    'discount': round(((regular - current) / regular) * 100, 1)
                })

            # Promotional deals
            promos = user.get('promotions', [])
            claimable = [p for p in promos if p.get('canClaim')]

            if claimable:
                best = min(claimable, key=lambda x: x['price'])
                if best['price'] < regular:
                    deals.append({
                        'username': user['username'],
                        'type': 'promotional',
                        'regular_price': regular,
                        'promo_price': best['price'],
                        'discount': round(((regular - best['price']) / regular) * 100, 1),
                        'expires': best.get('endsAt')
                    })

        # Sort by discount percentage
        deals.sort(key=lambda x: x['discount'], reverse=True)
        return deals

# Usage
api = OnlyFansAPI(
    auth_id="your_auth_id",
    sess="your_session",
    user_agent="your_user_agent",
    x_bc="your_x_bc_token"
)

deals = api.find_deals()
for deal in deals[:10]:  # Top 10 deals
    print(f"{deal['username']}: {deal['discount']}% off - ${deal.get('sale_price', deal.get('promo_price'))}")
```

---

## Security & Legal Considerations

1. **Authentication Data:** Never share or expose your `auth.json` credentials
2. **Terms of Service:** Using this API may violate OnlyFans Terms of Service
3. **Rate Limiting:** Respect rate limits to avoid account restrictions
4. **Personal Use:** This documentation is for educational/personal use only
5. **Dynamic Rules:** Signature rules change periodically and must be fetched from external sources

---

## Additional Notes

- All timestamps are in ISO 8601 format with timezone
- Prices are in USD (or account currency)
- Media URLs may be CDN links with expiration
- Some endpoints require specific subscription status
- The API structure may change without notice

---

**Generated from:** OF-Scraper Repository Analysis
**Last Updated:** 2025-10-06