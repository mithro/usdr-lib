# usdr-lib — welland packaging fork

A fork of [wavelet-lab/usdr-lib](https://github.com/wavelet-lab/usdr-lib) that
adds **Debian 13 (trixie) packaging CI** and publishes a signed apt repository to
GitHub Pages, consumed by the welland fleet through the site apt proxy.

Upstream is unchanged; this fork adds only:

| Path | Purpose |
|---|---|
| `.github/workflows/deb.yml` | Native arm64 + amd64 `.deb` build in a `debian:trixie` container, then a signed flat apt repo published to Pages |
| `packaging/deb-version.py` | Derives the Debian version from the **pinned** upstream commit |
| `README.welland.md` | This file |

## Why a fork exists at all

Upstream ships packages for Ubuntu (PPA) and Debian 12 bookworm only — see their
[releases](https://github.com/wavelet-lab/usdr-lib/releases), whose assets stop
at `usdr_0.9.9.bookworm0.arm64.tar`. The welland fleet runs **Debian 13 trixie**,
and the last upstream tag (v0.9.9, January 2025) predates ~20 months of fixes
that matter for recent hardware such as the XSDR.

## Why a snapshot, not the tag

`packaging/deb-version.py` pins `UPSTREAM_COMMIT` and derives
`0.9.10b~git<date>.<sha>-0+welland1` from it. Upstream's own changelog already
reads "Switching to 0.9.10b", so the `~git` suffix sorts **below** an eventual
official `0.9.10b` and **above** `0.9.9` — a re-pin re-versions deterministically,
and packaging commits layered on top do not change the version.

## Why the arm64 leg must be native

Unlike `dtbocfg` (whose DKMS package is `Architecture: all`, so an amd64 runner
suffices), usdr's packages are architecture-specific: `libusdr`,
`soapysdr-module-usdr`, `usdr-tools` and `usdr-dkms` are all `amd64 arm64`. The
workflow therefore builds the arm64 leg on `ubuntu-24.04-arm`.

## Debian packaging is NOT vendored

Upstream keeps its `debian/` under `packaging/debian-bookworm`. The workflow
copies it to `debian/` at build time rather than forking it, so upstream
packaging fixes are picked up automatically. trixie is bookworm+1 and the
packaging is plain debhelper 13, so it applies unmodified — verified by a local
build in a clean trixie chroot before this CI was written.

`usdr-dmonitor` is deliberately **not published**: it is a PyQt5 GUI debug tool
and would drag a desktop stack onto headless fleet hosts.

## Consuming it

```bash
curl -fsSL https://mithro.github.io/usdr-lib/usdr.gpg \
  | sudo tee /etc/apt/keyrings/mithro-usdr.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/mithro-usdr.gpg] https://mithro.github.io/usdr-lib/ ./" \
  | sudo tee /etc/apt/sources.list.d/mithro-usdr.list
sudo apt update
sudo apt install usdr-tools usdr-dkms soapysdr-module-usdr
```

On the welland fleet this is done by the `usdr` Ansible role and an
`apt_sources_extra` entry in host_vars, fetched through
`https://apt-proxy.<site>.mithis.com/usdr/` (which needs a `Remap-usdr` in
`roles/apt_proxy`) rather than hitting Pages directly.

## Repo setup checklist (one-off)

1. Settings → Pages → Source: **GitHub Actions**
2. Settings → Secrets and variables → Actions → new secret
   `APT_GPG_PRIVATE_KEY` = the armoured private key
   (`~/.gnupg/apt-signing/usdr-apt-signing.private.asc`)
3. Push `welland-packaging` — the workflow triggers on that branch
