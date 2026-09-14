# Packaging validation

Validation performed on 2026-09-14:

- Eight standard-library unit tests passed, covering model rejection, missing/corrupt firmware rejection, firmware filename variants, narrowly scoped UCM editing, identical firmware aliases, service ordering, snapshot/rollback restoration, and dry-run non-mutation.
- The extraction script unpacked the official ASUS V6.3.1.15 executable and verified both firmware hashes without executing Windows code.
- The installer dry run passed on the documented HN7306EAC using the verified firmware.
- Shell syntax and CLI help checks passed.
- Relative Markdown links resolved.

A first dry run rejected the post-recovery subsystem ID. A read of sysfs showed `0xffff`, while vendor/device remained `0x1022:0x15e2` and the model remained HN7306EAC. The guard was updated to accept only the two observed subsystem values on that exact model and controller. The investigation records this observation without claiming its underlying cause is known.

The install, recovery, and rollback commands in this newly packaged utility were not run against the live system. The existing manually installed repair was left in place. Rollback was exercised with temporary files and mocked service calls. CI results are pending publication and execution on GitHub.

Confirmed audible playback belongs to the manual repair documented in INVESTIGATION.md. Clean installation, reboot, and suspend/resume remain separate hardware tests to complete.
