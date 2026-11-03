# Media recovery and version audit

This runner is invoked only through the restricted media-recovery SSH key. It performs bounded NFS, media-read and HLS checks. Its recovery boundary excludes Emby: Emby is observation-only; only Tunarr recovery is allowlisted.

The JSON report includes `installed_images` for Emby and both separate Tunarr instances. n8n consumes that field for a daily version audit. The runner does **not** contact registries, update images or restart Emby.

Deploy source through the controlled PC6 media-recovery procedure. Do not run Docker commands manually.
