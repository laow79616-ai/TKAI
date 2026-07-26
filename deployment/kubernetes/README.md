# TKAI Kubernetes manifests

The Helm chart in `deployment/helm/tkai` is the deployable source of truth.
These directories document resource ownership and provide static validation
anchors. Generate complete manifests with:

```powershell
helm template tkai deployment/helm/tkai --namespace tkai --create-namespace
```

No Secret object containing credentials or certificates is committed. Create
the referenced Secrets through an external secret controller or deployment
pipeline.
