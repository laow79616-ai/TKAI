# Kubernetes and Helm

## Architecture

TKAI runs API, dashboard, and gateway as rolling Deployments. PostgreSQL is an
optional, bounded single-replica StatefulSet; production installations should
normally set `postgresql.enabled=false` and configure a managed endpoint.
Observability workloads remain internal. NetworkPolicy defaults to deny.

## Install

```powershell
helm lint deployment/helm/tkai
helm template tkai deployment/helm/tkai -f deployment/helm/tkai/values-production.yaml
helm upgrade --install tkai deployment/helm/tkai --namespace tkai --create-namespace -f deployment/helm/tkai/values-production.yaml
```

Set real image repositories/tags, hostname, TLS Secret, storage classes, and
existing Secret names in a private values file. Never commit that file.

## Ingress and TLS

Ingress routes `/api` and `/health` to the API and `/` to the dashboard.
SSL redirect is enabled. Metrics have no Ingress route. TLS material is read
only from `ingress.tlsSecretName`.

## Scaling and availability

API and dashboard have bounded CPU/memory HPAs, anti-affinity, rolling updates,
three probe types, resource limits, and disruption budgets. Tune minimums and
maximums based on measured capacity. Nginx replicas are configurable.

## Secrets and persistent storage

Create PostgreSQL, Grafana, and TLS Secrets using an external secrets operator
or CI secret store. The reference PostgreSQL StatefulSet uses a PVC and exposes
a backup-controller annotation as an integration point. It does not implement
database HA or backups.

## Upgrades and rollback

```powershell
helm upgrade tkai deployment/helm/tkai --namespace tkai -f deployment/helm/tkai/values-production.yaml
helm history tkai --namespace tkai
helm rollback tkai <revision> --namespace tkai
```

Render and review manifests before upgrades. Back up external state first.

## Observability

The chart supplies Prometheus discovery, availability/restart/replica alerts,
Grafana, Loki, Alertmanager, and an optional ServiceMonitor for clusters with
the Prometheus Operator CRDs.

## Troubleshooting

```powershell
kubectl -n tkai get deploy,statefulset,pods,svc,ingress,hpa,pdb
kubectl -n tkai describe pod <pod>
kubectl -n tkai logs deployment/tkai-api --all-containers
helm status tkai --namespace tkai
```

For managed PostgreSQL, disable the StatefulSet, set `externalHost`, and provide
the referenced Secret key. Confirm DNS, NetworkPolicy, TLS, and migration
permissions before upgrading.
