# CT340 additional services

## LiteLLM

LiteLLM runs as the `litellm` container on port 4000. Its configuration is mounted from `/opt/litellm/config.yaml` and must remain mode 600, readable by the container user. The configuration must not enable `dangerously_permit_weak_or_unset_master_key`; a valid master key is required for authenticated API access.

Health verification:

- `/health/liveliness` must return HTTP 200.
- `/v1/models` must require authentication and therefore must not return HTTP 200 without credentials.
