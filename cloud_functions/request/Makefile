PROJECT = $(CURDIR)

all: run

.PHONY: build run docker test test-remote hmac

build:
	pack build \
	 --builder gcr.io/buildpacks/builder:v1 \
	 --env GOOGLE_FUNCTION_SIGNATURE_TYPE=http \
	 --env GOOGLE_FUNCTION_TARGET=request_handler \
	 request

run:
	DISABLE_GOOGLE_LOGGING=1 HMAC_KEY=secret GOOGLE_PROJECT=abc-12345 GOOGLE_REGION=us-west1 NOTIFICATION_WORKFLOW=12345 LOG_LEVEL=INFO \
		functions-framework --target request_handler --debug

docker:
	docker run --rm -p 8080:8080 request

test:
	curl http://127.0.0.1:8080 -w "%{http_code}" -X POST -H 'Content-Type: application/json' -H "x-tfe-notification-signature: 387e856a8a8bcbd8f9f8b6368713530b9ca662fb15ece81cb467e636cb0c5f068a11fce0cd4324855d66513f9d95e639cb3e2209690450409d89b9803ee7f9d8" -d @testing/data.json

test-remote:
	curl $(URL) -w "%{http_code}" -X POST -H 'Content-Type: application/json' -H "x-tfe-notification-signature: 387e856a8a8bcbd8f9f8b6368713530b9ca662fb15ece81cb467e636cb0c5f068a11fce0cd4324855d66513f9d95e639cb3e2209690450409d89b9803ee7f9d8" -d @testing/data.json

hmac:
	cat  testing/data.json | openssl dgst -sha512 -hmac "secret"
