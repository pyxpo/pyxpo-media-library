from __future__ import annotations

import asyncio

import pytest

from pyxpo.apis import _bridge
from pyxpo_media_library import MediaLibrary


class FakeApp:
    """Records native calls and answers from `handlers[(module, method)]`."""

    loop = None

    def __init__(self, handlers):
        self.handlers = handlers
        self.calls = []

    def call(self, module, method, *args, reply=False):
        self.calls.append((module, method, args))
        fut = asyncio.get_event_loop().create_future()
        out = self.handlers[(module, method)](*args)
        if isinstance(out, Exception):
            fut.set_exception(out)
        else:
            fut.set_result(out)
        return fut


def run(handlers, coro_fn):
    app = FakeApp(handlers)
    old = _bridge.get_app()
    _bridge.set_app(app)
    try:
        return asyncio.run(coro_fn()), app
    finally:
        _bridge.set_app(old)


def test_library_save_shape():
    _, app = run({("MediaLibrary", "save"): lambda p: None}, lambda: MediaLibrary.saveToLibraryAsync("/a.jpg"))
    assert app.calls[0][:2] == ("MediaLibrary", "save")


def test_library_permissions_expo_shape_and_default_is_read_write():
    h = {("MediaLibrary", "request_permission"): lambda w: {"status": "granted", "canAskAgain": True, "accessPrivileges": "limited"},
         ("MediaLibrary", "get_permission"): lambda w: {"status": "undetermined", "canAskAgain": True}}
    out, app = run(h, lambda: MediaLibrary.requestPermissionsAsync())
    assert out == {"status": "granted", "granted": True, "canAskAgain": True, "expires": "never", "accessPrivileges": "limited"}
    assert app.calls[0][2] == (False,)
    out, app = run(h, lambda: MediaLibrary.get_permissions_async(writeOnly=True))
    assert out == {"status": "undetermined", "granted": False, "canAskAgain": True, "expires": "never", "accessPrivileges": "none"}
    assert app.calls[0][:3] == ("MediaLibrary", "get_permission", (True,))
    out, _ = run({("MediaLibrary", "get_permission"): lambda w: {"status": "denied", "canAskAgain": False}},
                 lambda: MediaLibrary.getPermissionsAsync())
    assert out["granted"] is False and out["canAskAgain"] is False and out["accessPrivileges"] == "none"
    with pytest.raises(ValueError):  # a bad native status is not passed through
        run({("MediaLibrary", "get_permission"): lambda w: {"status": "maybe"}}, lambda: MediaLibrary.getPermissionsAsync())


def test_library_create_asset_validates_before_native_call():
    asset = {"id": "1", "uri": "content://media/1", "mediaType": "video", "width": 1920, "height": 1080,
             "duration": 2.5, "filename": "clip.mp4"}
    out, app = run({("MediaLibrary", "create"): lambda p: asset}, lambda: MediaLibrary.createAssetAsync("file:///c/clip.mp4"))
    assert out == asset and app.calls[0][2] == ("file:///c/clip.mp4",)
    for bad in ("", None, "https://x.dev/a.jpg", "content://media/1"):
        with pytest.raises(ValueError):
            run({}, lambda: MediaLibrary.createAssetAsync(bad))
        with pytest.raises(ValueError):
            run({}, lambda: MediaLibrary.saveToLibraryAsync(bad))
