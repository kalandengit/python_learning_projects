# Docker Makefile for building and testing the official Kalanfa Docker image
# Run from the docker/ directory to limit build context

.PHONY: build build-latest build-version run clean test

# Default image name
IMAGE_NAME ?= kalanfa
KALANFA_VERSION ?= latest
KALANFA_VERSION_SPEC ?=
CONTAINER_CLI ?= docker

ifneq (latest,$(KALANFA_VERSION))
	KALANFA_VERSION_SPEC = "==$(KALANFA_VERSION)"
endif

ifeq (, $(shell command -v $(CONTAINER_CLI) 2>/dev/null))
	CONTAINER_CLI = podman
endif

# Build the Docker image with docker/ as context
build:
	$(CONTAINER_CLI) build \
		-t $(IMAGE_NAME):$(KALANFA_VERSION) \
		--build-arg KALANFA_VERSION=$(KALANFA_VERSION) \
		--build-arg KALANFA_VERSION_SPEC=$(KALANFA_VERSION_SPEC) \
		-f Dockerfile .

# Build with as specific version
build-%:
	$(MAKE) build KALANFA_VERSION=$(subst build-,,$@)

# Run container for testing (requires volume mount)
run:
	$(CONTAINER_CLI) run --rm -it \
		-v /tmp/kalanfa-test:/kalanfa \
		-p 8080:8080 \
		-p 8081:8081 \
		$(IMAGE_NAME):$(KALANFA_VERSION)

# Test that container refuses to start without volume mount
test-mount-check:
	@echo "Testing mount validation (should fail)..."
	@$(CONTAINER_CLI) run --rm $(IMAGE_NAME):local 2>&1 | grep -q "must be a mounted volume" && \
		echo "PASS: Container correctly refused to start without volume mount" || \
		(echo "FAIL: Container should have refused to start"; exit 1)

# Clean up local images
clean:
	$(CONTAINER_CLI) rmi $(IMAGE_NAME):latest 2>/dev/null || true
