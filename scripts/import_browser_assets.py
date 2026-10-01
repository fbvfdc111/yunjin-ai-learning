from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/official/web_images"

BUNDLES = {
    "brocades_page1": Path(r"C:\Users\cyj\AppData\Local\Temp\browser-use\assets\a5d4dcb2-652d-4adc-8efc-e6a2f9e9f75e\manifest.json"),
    "world_tapestry": Path(r"C:\Users\cyj\AppData\Local\Temp\browser-use\assets\5430a4dc-c421-4674-bfef-975916ced9fa\manifest.json"),
    "fine_art": Path(r"C:\Users\cyj\AppData\Local\Temp\browser-use\assets\bdae0b8f-0275-43cd-b40e-2f4c77396478\manifest.json"),
}


def main() -> None:
    for group, manifest_path in BUNDLES.items():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        group_dir = DEST / group
        group_dir.mkdir(parents=True, exist_ok=True)
        for asset in payload["assets"]:
            source = Path(asset["path"])
            target = group_dir / asset["name"]
            shutil.copy2(source, target)
        shutil.copy2(manifest_path, group_dir / "browser_asset_manifest.json")
        print(f"{group}: {len(payload['assets'])} assets")


if __name__ == "__main__":
    main()

