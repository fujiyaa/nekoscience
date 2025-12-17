use crate::external::osu_auth::OsuAuth;
use crate::external::osu_forum_api::OsuApi;
use anyhow::{Result, anyhow};
use std::sync::Arc;

pub async fn init_osu_api() -> Result<Arc<OsuApi>> {
    let auth = OsuAuth::new();

    let token = auth
        .get_token_with_retry(10, 3)
        .await
        .ok_or_else(|| anyhow!("Failed to obtain Osu API token after 3 attempts"))?;

    Ok(Arc::new(OsuApi::new(token)))
}
