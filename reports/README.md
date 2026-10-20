# Runtime Evidence Reports Directory

This directory holds runtime execution artifacts dynamically produced by the 9-stage CI/CD pipeline (`.gitlab-ci.yml`) and local test executions.

All `.json`, `.xml`, and `.md` receipt files in this directory are ephemeral and generated on-the-fly during pipeline execution. They are captured as GitLab CI/CD job artifacts and must not be committed to source control.
