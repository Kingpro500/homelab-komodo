// Kept in version control so Homepage never needs to create this file at runtime.
// The config dir is bind-mounted read-only; without this file existing, Homepage
// tries to copy its skeleton here, fails with EROFS, and exits (code 1) -> restart loop.
