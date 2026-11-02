use std::fs;
use zed_extension_api::{self as zed, Result, settings::LspSettings};

const SERVER_VERSION: &str = "v0.88.0";

fn release_target(os: zed::Os, arch: zed::Architecture) -> Result<&'static str> {
    match (os, arch) {
        (zed::Os::Mac, zed::Architecture::Aarch64) => Ok("aarch64-apple-darwin"),
        (zed::Os::Linux, zed::Architecture::X8664) => Ok("x86_64-unknown-linux-musl"),
        (zed::Os::Windows, zed::Architecture::X8664) => Ok("x86_64-pc-windows-msvc"),
        _ => Err("VHDL LS has no bundled release for this platform. Set lsp.vhdl_ls.binary.path to a native vhdl_ls executable.".into()),
    }
}

struct Vhdl;

impl Vhdl {
    fn installed_server(&self, id: &zed::LanguageServerId) -> Result<String> {
        let (os, arch) = zed::current_platform();
        let target = release_target(os, arch)?;
        let directory = format!("vhdl_ls-{SERVER_VERSION}");
        let executable = if os == zed::Os::Windows {
            "vhdl_ls.exe"
        } else {
            "vhdl_ls"
        };
        let path = format!("{directory}/vhdl_ls-{target}/bin/{executable}");
        if fs::metadata(&path).is_ok_and(|metadata| metadata.is_file()) {
            return Ok(path);
        }

        zed::set_language_server_installation_status(
            id,
            &zed::LanguageServerInstallationStatus::CheckingForUpdate,
        );
        let release = zed::github_release_by_tag_name("VHDL-LS/rust_hdl", SERVER_VERSION)?;
        let asset_name = format!("vhdl_ls-{target}.zip");
        let asset = release
            .assets
            .iter()
            .find(|asset| asset.name == asset_name)
            .ok_or_else(|| {
                format!("VHDL LS {SERVER_VERSION} is missing release asset {asset_name}")
            })?;
        zed::set_language_server_installation_status(
            id,
            &zed::LanguageServerInstallationStatus::Downloading,
        );
        // Retain the archive's layout: the server locates IEEE libraries beside bin/.
        zed::download_file(
            &asset.download_url,
            &directory,
            zed::DownloadedFileType::Zip,
        )?;
        zed::make_file_executable(&path)?;
        Ok(path)
    }
}

impl zed::Extension for Vhdl {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        let settings = LspSettings::for_worktree(id.as_ref(), worktree)?;
        let binary = settings.binary;
        let command = if let Some(path) = binary.as_ref().and_then(|binary| binary.path.clone()) {
            path
        } else if let Some(path) = worktree.which("vhdl_ls") {
            path
        } else {
            self.installed_server(id)?
        };
        let args = binary
            .as_ref()
            .and_then(|binary| binary.arguments.clone())
            .unwrap_or_default();
        let mut env = worktree.shell_env();
        if let Some(overrides) = binary.and_then(|binary| binary.env) {
            env.retain(|(key, _)| !overrides.contains_key(key));
            env.extend(overrides);
        }
        Ok(zed::Command { command, args, env })
    }

    fn language_server_initialization_options(
        &mut self,
        id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<Option<zed::serde_json::Value>> {
        Ok(LspSettings::for_worktree(id.as_ref(), worktree)?.initialization_options)
    }

    fn language_server_workspace_configuration(
        &mut self,
        id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<Option<zed::serde_json::Value>> {
        Ok(LspSettings::for_worktree(id.as_ref(), worktree)?.settings)
    }
}

zed::register_extension!(Vhdl);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn native_release_targets() {
        assert_eq!(
            release_target(zed::Os::Mac, zed::Architecture::Aarch64).unwrap(),
            "aarch64-apple-darwin"
        );
        assert_eq!(
            release_target(zed::Os::Windows, zed::Architecture::X8664).unwrap(),
            "x86_64-pc-windows-msvc"
        );
        assert!(release_target(zed::Os::Mac, zed::Architecture::X8664).is_err());
        assert!(release_target(zed::Os::Linux, zed::Architecture::Aarch64).is_err());
    }
}
