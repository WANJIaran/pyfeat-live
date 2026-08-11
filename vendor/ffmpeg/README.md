# Bundled FFmpeg for Windows

Windows release builds download the FFmpeg 8.1 `win64-lgpl-shared` artifact from
[BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds). The workflow
verifies the SHA-256 digest supplied by the GitHub Release API before copying
the shared DLLs into the Tauri bundle.

The DLLs are required by TorchCodec and are added only to the Python sidecar's
`PATH`. They are not checked into this repository.

FFmpeg is licensed under the GNU Lesser General Public License (LGPL) for this
build variant. BtbN's build scripts are MIT-licensed. Source and build scripts
are available from the linked repository, which in turn links to FFmpeg's
upstream source and license information.
