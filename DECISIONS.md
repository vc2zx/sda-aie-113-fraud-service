# Engineering Decisions

## 1. Isolate the ML framework behind an adapter

### Context
The original notebook directly loaded and called the scikit-learn model.

### Decision
The application core depends on a model interface, while joblib, pandas, and scikit-learn are isolated in `adapters/sklearn_model.py`.

### Trade-off
This introduces more abstraction than calling the model directly from the API.

### Consequence
Domain and service logic can be tested independently, and the model implementation can change without rewriting business logic.

---

## 2. Enforce strict validation at the API boundary

### Context
Automatic type coercion can allow malformed or ambiguous production inputs.

### Decision
The API forbids unknown fields and applies explicit bounds, identifier patterns, strict numeric validation, and timestamp validation.

### Trade-off
Some technically coercible inputs are deliberately rejected.

### Consequence
Malformed data fails predictably with a 4xx response before reaching the model.

---

## 3. Load and warm the model during startup

### Context
Loading the model on the first prediction request would increase first-request latency and delay configuration failures.

### Decision
The model is loaded during the FastAPI lifespan and a warm-up prediction runs before readiness becomes true.

### Trade-off
Application startup takes longer.

### Consequence
The service fails fast and `/v1/ready` represents actual serving readiness.

---

## 4. Use a multi-stage non-root container

### Context
The naive Docker image was large and ran with unnecessary privileges.

### Decision
Use a multi-stage build, slim runtime image, dependency-layer caching, non-root application user, and health checks.

### Trade-off
The Dockerfile is more complex.

### Consequence
Measured image content size decreased from 539 MB to 257 MB while improving runtime security and build caching.

---

## 5. Treat model behaviour and releases as production contracts

### Context
Code coverage alone cannot detect model skew or identify exactly which application version produced a deployment.

### Decision
Use behavioural and golden-score tests in CI and publish images using immutable Git SHA tags rather than `latest`.

Structured logs include model version and Git SHA while excluding raw sensitive transaction data.

### Trade-off
CI performs additional checks and approved behavioural expectations must be maintained deliberately.

### Consequence
Unexpected scoring changes are detected before release and every published image maps to a specific source revision.