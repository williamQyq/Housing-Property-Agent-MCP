PROJECT_ID ?= fresh-ward-425622-h9
REGISTRY ?= gcr.io
IMAGE_TAG ?= latest
KUBECONFIG ?= $(HOME)/.kube/k3s.yaml
KUBECTL := kubectl --kubeconfig $(KUBECONFIG)
GCR_KEYFILE ?= k8s/gcr-keyfile.json

FRONTEND_DIR := frontend
FRONTEND_IMAGE := $(REGISTRY)/$(PROJECT_ID)/frontend:$(IMAGE_TAG)

SERVICES_DIR := services
SERVICES := $(shell find $(SERVICES_DIR) -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)

.PHONY: podman-ensure podman-build podman-push podman-release podman-build-frontend podman-push-frontend podman-release-frontend k8s-deploy

podman-ensure:
	@podman info >/dev/null 2>&1 || { \
		if podman machine list >/dev/null 2>&1; then \
			echo "Podman machine not running; attempting to start..."; \
			if podman machine start >/dev/null 2>&1; then \
				if ! podman info >/dev/null 2>&1; then \
					echo "Podman still unavailable after starting machine."; \
					echo "Run 'podman machine init' (first time) then 'podman machine start'."; \
					exit 1; \
				fi; \
			else \
				echo "Failed to start Podman machine automatically."; \
				echo "Run 'podman machine init' (first time) then 'podman machine start'."; \
				exit 1; \
			fi; \
		else \
			echo "Podman daemon not reachable."; \
			echo "Ensure Podman is installed and its service is running."; \
			exit 1; \
		fi; \
	}

podman-build:
	@$(MAKE) podman-build-frontend
	@set -e; \
	for svc in $(SERVICES); do \
		image="$(REGISTRY)/$(PROJECT_ID)/$$svc:$(IMAGE_TAG)"; \
		context="$(SERVICES_DIR)/$$svc"; \
		echo "Building service image: $$image"; \
		podman build --tag $$image $$context; \
	done

podman-push:
	@$(MAKE) podman-push-frontend
	@set -e; \
	for svc in $(SERVICES); do \
		image="$(REGISTRY)/$(PROJECT_ID)/$$svc:$(IMAGE_TAG)"; \
		echo "Pushing service image: $$image"; \
		podman push $$image; \
	done

podman-release:
	@$(MAKE) podman-build
	@$(MAKE) podman-push

podman-build-frontend:
	@$(MAKE) podman-ensure
	@echo "Building frontend image: $(FRONTEND_IMAGE)"
	podman build --tag $(FRONTEND_IMAGE) $(FRONTEND_DIR)

podman-push-frontend:
	@$(MAKE) podman-ensure
	@echo "Pushing frontend image: $(FRONTEND_IMAGE)"
	podman push $(FRONTEND_IMAGE)

podman-release-frontend:
	@$(MAKE) podman-build-frontend
	@$(MAKE) podman-push-frontend

k8s-deploy:
	@[ -f $(GCR_KEYFILE) ] || { echo "Missing GCR key file: $(GCR_KEYFILE)"; exit 1; }
	@$(KUBECTL) create secret docker-registry gcr-json-key \
		--docker-server=https://gcr.io \
		--docker-username=_json_key \
		--docker-password="$$\(cat $(GCR_KEYFILE)\)" \
		--docker-email=qyqfiles@gmail.com \
		--dry-run=client -o yaml | $(KUBECTL) apply -f -
	@$(KUBECTL) apply -f k8s/frontend/
