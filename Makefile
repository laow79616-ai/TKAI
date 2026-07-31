.PHONY: validate enterprise-validate dev-up dev-down dev-logs dev-reset observability-up observability-down observability-status observability-logs helm-lint helm-template kubernetes-validate kubernetes-install kubernetes-upgrade kubernetes-uninstall kubernetes-status kubernetes-logs

validate enterprise-validate:
	python scripts/validate-enterprise.py

dev-up:
	docker compose up --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

dev-reset:
	docker compose down -v --remove-orphans

OBSERVABILITY_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.observability.yml

observability-up:
	$(OBSERVABILITY_COMPOSE) up --build -d

observability-down:
	$(OBSERVABILITY_COMPOSE) down

observability-status:
	$(OBSERVABILITY_COMPOSE) ps

observability-logs:
	$(OBSERVABILITY_COMPOSE) logs -f prometheus grafana loki alloy alertmanager postgres-exporter nginx-exporter

HELM_CHART = deployment/helm/tkai
KUBE_NAMESPACE ?= tkai
HELM_RELEASE ?= tkai

helm-lint:
	helm lint $(HELM_CHART)

helm-template:
	helm template $(HELM_RELEASE) $(HELM_CHART) --namespace $(KUBE_NAMESPACE)

kubernetes-validate:
	helm template $(HELM_RELEASE) $(HELM_CHART) --namespace $(KUBE_NAMESPACE) | kubectl apply --dry-run=client -f -

kubernetes-install:
	helm upgrade --install $(HELM_RELEASE) $(HELM_CHART) --namespace $(KUBE_NAMESPACE) --create-namespace

kubernetes-upgrade:
	helm upgrade $(HELM_RELEASE) $(HELM_CHART) --namespace $(KUBE_NAMESPACE)

kubernetes-uninstall:
	helm uninstall $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE)

kubernetes-status:
	kubectl --namespace $(KUBE_NAMESPACE) get deployments,statefulsets,pods,services,ingress,hpa,pdb

kubernetes-logs:
	kubectl --namespace $(KUBE_NAMESPACE) logs deployment/tkai-api --all-containers --tail=200
