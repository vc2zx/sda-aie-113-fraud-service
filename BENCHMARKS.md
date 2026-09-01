# Benchmarks

## Lab 2 — API Load Test

### Environment

- Endpoint: `POST /v1/predict`
- Tool: `hey`
- Requests: 1000
- Concurrency: 20
- Model version: `v3.2.0`

### Load Test Command

```powershell
.\hey.exe -n 1000 -c 20 `
  -m POST `
  -H "Content-Type: application/json" `
  -D payloads\sample.json `
  http://127.0.0.1:8000/v1/predict
```

### Results

| Metric | Result |
|---|---:|
| Requests | 1000 |
| Successful responses | 1000 |
| Requests/sec | 137.1847 |
| Average latency | 145.4 ms |
| p50 latency | 138.8 ms |
| p90 latency | 175.8 ms |
| p95 latency | 193.1 ms |
| p99 latency | 324.2 ms |
| Fastest | 97.1 ms |
| Slowest | 368.7 ms |
| Total duration | 7.2894 s |

All 1000 requests returned HTTP `200`.

---

## Lab 3 — Container Benchmarks

### Image Size

| Image | Disk Usage | Content Size |
|---|---:|---:|
| Naive | 2.17 GB | 539 MB |
| Multi-stage | 923 MB | 257 MB |

The multi-stage image reduced content size by approximately **52.3%** compared with the naive image.

### Build Time

| Build | Time |
|---|---:|
| Naive initial build | ~9 min |
| Multi-stage initial build | 189.43 s (~3 min 9 s) |
| Fully cached rebuild (no source change) | 2.12 s |
| Warm rebuild after source change | 32.44 s |

The dependency-installation layer remained cached during the source-code rebuild, and the warm rebuild completed in under one minute.

### Runtime Verification

- Runtime user: `app`
- API container health: `healthy`
- Redis container health: `healthy`
- `/v1/ready`: HTTP `200`
- `/v1/predict`: HTTP `200`
- Model version: `v3.2.0`

### Container Prediction Latency

Five sequential requests to `POST /v1/predict` were measured:

| Request | Latency |
|---|---:|
| 1 | 12.758 ms |
| 2 | 17.841 ms |
| 3 | 12.809 ms |
| 4 | 11.181 ms |
| 5 | 12.783 ms |
| Average | **13.47 ms** |

These sequential container measurements are not directly comparable with the Lab 2 `hey` latency results because the Lab 2 benchmark used 20 concurrent workers.

### Time to Ready

Measured from `docker-compose up -d` until the API container reported `healthy`.

- Time to ready: **13.21 s**
