# Changelog

## Unreleased

- Moved to its own repository, github.com/pyxpo/pyxpo-media-library, with CI on Python 3.9 and 3.12 and releases from tags.
- Added a security policy, a contributing guide and issue templates.
- Real permissions: `getPermissionsAsync` / `requestPermissionsAsync` return expo's response with `accessPrivileges`; `writeOnly` now defaults to `False` (expo default).
- `createAssetAsync(uri)`; photos and videos on both platforms (`saveToLibraryAsync` too).

## 0.1.0a1

- Docs: detailed README with screenshots, and fuller PyPI metadata (keywords, classifiers, project URLs).
- First release.
