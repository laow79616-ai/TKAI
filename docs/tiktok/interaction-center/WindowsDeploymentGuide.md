# Windows Deployment Guide

Install the repository's existing Python and frontend dependencies, run the standard
TKAI API service, and build `dashboard/frontend` and `studio/frontend` with
`npm run build`. The Interaction Center requires no separate daemon or secret and
uses the existing Docker Compose and Kubernetes deployments.
