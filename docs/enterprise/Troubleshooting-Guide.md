# Troubleshooting Guide

Capture version, commit, environment, command, exit code, timestamps, and sanitized errors. Reproduce minimally, confirm dependencies/configuration, then run the full validator. For imports reinstall `-e ".[dev,server]"`; for frontends use `npm ci` then build; for archives rebuild from a clean commit. A secret finding requires immediate removal/rotation and history review. Never bypass a release gate.
