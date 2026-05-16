# Chocolatey Package for clob (Windows)

## Setup (Maintainer)

1. Create a Chocolatey account at chocolatey.org
2. Pack the package: `choco pack clob/clob.nuspec`
3. Test locally: `choco install clob --source "."`
4. Push to Chocolatey: `choco push clob.0.2.0.nupkg --source https://push.chocolatey.org`

## Installation (Users)

```powershell
choco install clob
```

## Update

```powershell
choco upgrade clob
```

## Uninstall

```powershell
choco uninstall clob
```

## Requirements

- Windows 10/11
- Chocolatey
- Python 3.12+ (`choco install python312`)
- Windows Terminal recommended

## Building Locally

```powershell
cd scripts/chocolatey
choco pack clob/clob.nuspec
choco install clob --source "." -y
clob --version
```
