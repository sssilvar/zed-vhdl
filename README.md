# VHDL for Zed

Native VHDL editing in Zed with semantic completion, hover, go to definition, references, rename, document symbols and live diagnostics from [VHDL LS](https://github.com/VHDL-LS/rust_hdl). Tree-sitter supplies highlighting, outlines, indentation, brackets and text objects. Snippets cover entities and clocked/combinational processes.

## Install for development

Install Rust through rustup, then run:

```sh
rustup target add wasm32-wasip2
```

In Zed, run **zed: install dev extension** from the command palette and select this repository. Zed compiles the extension and pinned Tree-sitter grammar. Open a project folder containing VHDL files. This dev extension uses the `vhdl` ID and replaces the registry VHDL extension while installed. Rebuild it from the Extensions view after changing its source.

The adapter first uses `lsp.vhdl_ls.binary.path`, then `vhdl_ls` on the project shell PATH, then downloads the official **VHDL LS v0.88.0** release. Apple Silicon macOS runs its native ARM64 binary. Linux x86_64 and Windows x86_64 release downloads are also configured; only macOS ARM64 has been exercised here. The downloaded archive retains its IEEE/std libraries and is cached for offline reuse. First installation needs network access; the server subsequently runs locally.

For platforms without an upstream release, install a native VHDL LS and point Zed to it. The same override can select a different server version:

```json
{
  "lsp": {
    "vhdl_ls": {
      "binary": {
        "path": "/absolute/path/to/vhdl_ls",
        "arguments": []
      }
    }
  }
}
```

`binary.env`, `initialization_options` and `settings` are forwarded through Zed's standard LSP configuration. Keep the server's accompanying `vhdl_libraries` directory when installing manually. A PATH or explicit override takes responsibility for its server version and library installation.

## Configure a project

Create `vhdl_ls.toml` in the folder opened by Zed:

```toml
standard = "2008"
preferred_case = "lower"

[libraries]
work.files = ["rtl/**/*.vhd", "sim/**/*.vhd"]
```

Add each design library under `[libraries]`, using paths relative to this file. IEEE and std libraries ship with the official server. See the [VHDL LS configuration reference](https://github.com/VHDL-LS/rust_hdl#configuration) for external libraries and diagnostic settings. The small `examples/blinker` project is ready to open directly.

Use Zed's **editor: show completions** command for suggestions, **editor: hover** for type information, and its normal definition/reference/rename commands. Completion details come directly from semantic analysis; no regular-expression rewriting is applied. Unknown symbols are reported as you edit. Correcting the source clears diagnostics.

This is an editor integration, not a synthesizer. It does not provide FPGA timing, placement, routing or synthesis diagnostics, nor a formatter or hardware debugger. Use project tasks to run your simulator and FPGA suite. Language coverage follows VHDL LS and the pinned Tree-sitter grammar; an editor-clean design is not a guarantee of synthesizability.

## Check changes

```sh
cargo fmt --check
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
cargo build --locked --target wasm32-wasip2
python3 tests/lsp_smoke.py /absolute/path/to/vhdl_ls
```

The smoke test uses the real server, checks IEEE-backed completion, hover, definition, rename and symbols, introduces and fixes an unresolved name, then completes the LSP shutdown handshake. Every response wait is bounded. An optional second argument points to a ZYBO project containing `blinker.vhd`, `vhdl_ls.toml` and optionally `tb_blinker.vhd`; the latter also checks navigation to `std.env.finish`. Files are copied to a temporary directory before editing.

Tested with Zed 1.26.2 and VHDL LS 0.88.0 on Apple Silicon macOS. The dev extension was installed through Zed, its server downloaded automatically, and semantic completion, declaration documentation, syntax highlighting, breadcrumbs and occurrence highlights were checked in a VHDL-2008 ZYBO project.

The adapter and queries in this repository are MIT licensed. The grammar is fetched from [alemuller/tree-sitter-vhdl](https://github.com/alemuller/tree-sitter-vhdl) at the revision pinned in `extension.toml`; the server comes from its official upstream release. Before public registry submission, coordinate with the existing VHDL extension as requested by [Zed's publishing prerequisites](https://zed.dev/docs/extensions/publishing/prerequisites).
