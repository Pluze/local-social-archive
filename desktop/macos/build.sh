#!/bin/zsh
set -euo pipefail

root_dir="${0:A:h}"
repo_dir="${root_dir:h:h}"
component_dir="${LOCAL_ARCHIVE_COMPONENT_DIR:-$repo_dir/components/provider}"
dist_dir="${LOCAL_ARCHIVE_DIST_DIR:-$repo_dir/dist}"
build_dir="$repo_dir/.build/macos"
stage_dir="$(mktemp -d /private/tmp/local-archive-assistant.XXXXXX)"
trap 'rm -rf -- "$stage_dir"' EXIT
info_plist="$root_dir/App/Info.plist"
[[ -f "$component_dir/Info.plist" ]] && info_plist="$component_dir/Info.plist"
executable="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$info_plist")"
display_name="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' "$info_plist")"
app_dir="$stage_dir/$display_name.app"

mkdir -p "$build_dir/module-cache" "$dist_dir" "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources/Web" "$app_dir/Contents/Resources/Tools" "$app_dir/Contents/Resources/Data"
export CLANG_MODULE_CACHE_PATH="$build_dir/module-cache"
export SWIFT_MODULECACHE_PATH="$build_dir/module-cache"

if [[ -f "$component_dir/prepare.sh" ]]; then
  zsh "$component_dir/prepare.sh" "$build_dir/component" "$app_dir/Contents/Resources/Tools"
fi

swiftc_bin="$(xcrun -f swiftc)"
sdk_path="$(xcrun --sdk macosx --show-sdk-path)"
"$swiftc_bin" -sdk "$sdk_path" -target arm64-apple-macosx13.0 -swift-version 5 -O -framework AppKit -framework Security -framework WebKit "$root_dir/App/CredentialStore.swift" "$root_dir/App/main.swift" "$component_dir/Adapter.swift" -o "$app_dir/Contents/MacOS/$executable"
cp "$info_plist" "$app_dir/Contents/Info.plist"
cp "$root_dir/Web/"* "$app_dir/Contents/Resources/Web/"
if [[ -d "$root_dir/Tools" ]]; then
  find "$root_dir/Tools" -maxdepth 1 -type f -exec cp {} "$app_dir/Contents/Resources/Tools/" \;
fi
if [[ -d "$component_dir/Tools" ]]; then
  find "$component_dir/Tools" -maxdepth 1 -type f -exec cp {} "$app_dir/Contents/Resources/Tools/" \;
fi

xattr -cr "$app_dir"
codesign --force --deep --sign - "$app_dir"
codesign --verify --deep --strict "$app_dir"
ditto -c -k --norsrc --keepParent "$app_dir" "$dist_dir/$display_name.zip"
echo "$app_dir"
echo "$dist_dir/$display_name.zip"
