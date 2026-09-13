# Normalized I/O Schema

## Input

```json
{
  "materials": {
    "text": "",
    "files": [{"name":"","kind":"image|pdf|presentation|document|text","text":"","url":""}],
    "links": [""]
  },
  "constraints": {
    "style": "AUTO|P01..P18",
    "aspect_ratio": "9:16|16:9|1:1",
    "count": 3,
    "language": "auto",
    "must_include": [],
    "must_avoid": []
  }
}
```

## Factual brief

```json
{
  "title":"", "subtitle":"", "theme":"", "date":"", "time":"",
  "location":"", "venue":"", "organizer":"", "audience":"", "cta":"",
  "phone":"", "address":"", "brand":"", "activity_type":"",
  "facts":[], "body":""
}
```

Hard facts come from user sources only. Do not infer missing phone/address/date/price/prize/organizer fields.

## Style decision

If the user supplies `Pxx`, use it. For `AUTO`, classify the activity and prefer:

- competition/hackathon/AI: P01, P02, P07, P11, P15, P16, P17, P18
- forum/exhibition/conference: P03, P04, P06, P09, P11, P14, P16
- culture/tourism/non-heritage: P04, P05, P09, P12, P13, P14
- merchant/membership/brand conversion: P07, P11, P14, P16
- conceptual/attitude-led: P08, P10, P13, P15, P17

Break ties using information density and real assets: architecture favors P01/P14/P16; youth people favor P18/P07; dense copy favors P03/P09/P11/P14/P16.

## Output

```json
{
  "selected_style":{"code":"P11","name":"对角主轴","source":"auto|user","reason":""},
  "variants":[
    {"id":"A","label":"地域/场景融合型","prompt":""},
    {"id":"B","label":"活动核心型","prompt":""},
    {"id":"C","label":"概念创意型","prompt":""}
  ],
  "aspect_ratio":"9:16",
  "final_pixels":"2160x3840"
}
```

If geography is not important, A becomes context/brand/venue-grounded rather than forcing landmarks. All variants stay in the same selected P-style unless the user explicitly asks for multiple styles.
