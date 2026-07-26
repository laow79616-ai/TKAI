{{- define "tkai.name" -}}tkai{{- end }}
{{- define "tkai.labels" -}}
app.kubernetes.io/name: tkai
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
{{- define "tkai.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile: {type: RuntimeDefault}
{{- end }}
{{- define "tkai.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities: {drop: ["ALL"]}
{{- end }}
