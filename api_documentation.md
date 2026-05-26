# API Endpoint Documentation

## Base URL

- **Local:** `http://localhost:5001`
- **Live:** `https://nlu-building-violations.onrender.com` *(update with actual URL)*

---

## 1. GET /property/{address}/

Retrieve violation history and scofflaw status for a given address.

### Request

```
GET /property/7120 S ROCKWELL ST/
```

- **Method:** GET
- **URL Parameter:** `address` (string) — the property address to look up
- **Request Body:** None

### Response — 200 OK

```json
{
    "address": "7120 S ROCKWELL ST",
    "last_violation_date": "2025-08-14",
    "violation_count": 2,
    "violations": [
        {
            "date": "2025-08-14",
            "code": "CN104035",
            "status": "OPEN",
            "description": "MAINTAIN WINDOW",
            "inspector_comments": "BASEMENT - WINDOWS PANES BROKEN.14X-3-303.13"
        },
        {
            "date": "2025-08-14",
            "code": "CN061014",
            "status": "OPEN",
            "description": "REPAIR EXTERIOR WALL",
            "inspector_comments": "REAR OF BUILDING - SIDING COMING APART.14X-3-303.6"
        }
    ],
    "SCOFFLAW": false
}
```

| Field | Type | Description |
|---|---|---|
| address | string | The normalized address |
| last_violation_date | string (YYYY-MM-DD) or null | Date of the most recent violation |
| violation_count | integer | Total number of violations for this address |
| violations | array of objects | All known violations (unordered) |
| violations[].date | string (YYYY-MM-DD) or null | Violation date |
| violations[].code | string | Violation code (e.g. "CN104035") |
| violations[].status | string | Status: "OPEN", "COMPLIED", or "NO ENTRY" |
| violations[].description | string or null | Short description of the violation |
| violations[].inspector_comments | string or null | Inspector's detailed comments |
| SCOFFLAW | boolean | Whether this address appears on the scofflaw list |

### Response — 404 Not Found

```json
{
    "error": "Address not found"
}
```

| Field | Type | Description |
|---|---|---|
| error | string | Error message |

---

## 2. POST /property/{address}/comments/

Submit a comment about a property address.

### Request

```
POST /property/7120 S ROCKWELL ST/comments/
Content-Type: application/json
```

**Request Body:**

```json
{
    "author": "John Doe",
    "comment": "This building has visible structural damage on the east wall."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| author | string | Yes | Name of the comment author (max 200 chars) |
| comment | string | Yes | Comment content (max 5000 chars) |

### Response — 201 Created

```json
{
    "message": "Comment created successfully",
    "id": 1,
    "created_at": "2025-05-23T14:30:00.000000"
}
```

| Field | Type | Description |
|---|---|---|
| message | string | Success confirmation |
| id | integer | Auto-generated comment ID |
| created_at | string (ISO 8601) | Server-generated timestamp |

### Response — 400 Bad Request

```json
{
    "error": "author is required and cannot be empty"
}
```

| Field | Type | Description |
|---|---|---|
| error | string | Validation error message |

### Response — 404 Not Found

```json
{
    "error": "Address not found in database"
}
```

Returned when the address does not exist in either the violations or scofflaws table. Comments can only be posted on known property addresses.

| Field | Type | Description |
|---|---|---|
| error | string | Error message |

---

## 3. GET /property/scofflaws/violations?since={yyyy-mm-dd}

Find scofflaw properties that have had violations on or after a given date.

### Request

```
GET /property/scofflaws/violations?since=2024-06-01
```

- **Method:** GET
- **Query Parameter:** `since` (string, format: YYYY-MM-DD) — the cutoff date (inclusive)
- **Request Body:** None

### Response — 200 OK

```json
{
    "since": "2024-06-01",
    "count": 15,
    "addresses": [
        "500 E 88TH ST",
        "7900 S DREXEL AVE",
        "4822 W MELROSE ST",
        "3793 S ARCHER AVE"
    ]
}
```

| Field | Type | Description |
|---|---|---|
| since | string (YYYY-MM-DD) | The date filter that was applied |
| count | integer | Number of matching addresses |
| addresses | array of strings | Scofflaw property addresses with violations since the given date |

### Response — 400 Bad Request

```json
{
    "error": "Query parameter 'since' is required (format: YYYY-MM-DD)"
}
```

or

```json
{
    "error": "Invalid date format. Use YYYY-MM-DD"
}
```

| Field | Type | Description |
|---|---|---|
| error | string | Validation error message |

---

## Notes

- **Address matching** is case-insensitive. Addresses are normalized (trimmed + uppercased) before lookup.
- **Input sanitization** on POST: whitespace is trimmed, control characters are removed, and max lengths are enforced. All database queries use parameterized statements to prevent SQL injection.
- **Null fields**: `violation_description` and `inspector_comments` may be `null` when the inspector did not provide that information.
