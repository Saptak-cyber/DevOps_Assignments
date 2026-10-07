{{/* Base name for every object: "<release>" if it already contains the chart name, else "<release>-clinicdesk". */}}
{{- define "clinicdesk.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "clinicdesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: clinicdesk
{{- end -}}

{{/* Selector labels for one component: include "clinicdesk.selectorLabels" (dict "ctx" . "component" "backend") */}}
{{- define "clinicdesk.selectorLabels" -}}
app.kubernetes.io/name: {{ .ctx.Chart.Name }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "clinicdesk.image" -}}
{{- $registry := .ctx.Values.global.imageRegistry -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry .image.repository (toString .image.tag) -}}
{{- else -}}
{{- printf "%s:%s" .image.repository (toString .image.tag) -}}
{{- end -}}
{{- end -}}

{{- define "clinicdesk.dbSecretName" -}}
{{- default (printf "%s-db" (include "clinicdesk.fullname" .)) .Values.database.existingSecret -}}
{{- end -}}

{{- define "clinicdesk.dbHost" -}}
{{- if .Values.postgres.enabled -}}
{{- printf "%s-postgres" (include "clinicdesk.fullname" .) -}}
{{- else -}}
{{- required "externalDatabase.host is required when postgres.enabled=false" .Values.externalDatabase.host -}}
{{- end -}}
{{- end -}}

{{- define "clinicdesk.podSecurity" -}}
automountServiceAccountToken: false
{{- with .ctx.Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
securityContext:
  runAsNonRoot: true
  runAsUser: {{ .uid }}
  runAsGroup: {{ .uid }}
  {{- if .fsGroup }}
  fsGroup: {{ .uid }}
  {{- end }}
  seccompProfile:
    type: RuntimeDefault
{{- end -}}

{{- define "clinicdesk.containerSecurity" -}}
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: {{ .readOnly }}
  capabilities:
    drop: [ALL]
{{- end -}}
