use std::time::Duration;
use tokio::sync::Mutex;
use serde::Deserialize;
use anyhow::Result;
use reqwest::{Client, StatusCode};
use dotenv::dotenv;
use std::env;
use tokio::time::{sleep, Instant};

#[derive(Debug, Deserialize)]
struct TokenResponse {
    access_token: String,
    expires_in: u64,
    token_type: String,
    scope: Option<String>,
}

pub struct OsuAuth {
    client_id: String,
    client_secret: String,
    client: Client,
    cached_token: Mutex<Option<CachedToken>>,
}

struct CachedToken {
    token: String,
    expires_at: Instant,
}

impl OsuAuth {
    pub fn new() -> Self {
        dotenv().ok();

        let client_id = env::var("OSU_CLIENT_ID")
            .expect("OSU_CLIENT_ID not set");
        let client_secret = env::var("OSU_CLIENT_SECRET")
            .expect("OSU_CLIENT_SECRET not set");

        Self {
            client_id,
            client_secret,
            client: Client::new(),
            cached_token: Mutex::new(None),
        }
    }

    pub async fn get_token(&self, timeout_sec: u64) -> Result<String> {
        {
            let cache = self.cached_token.lock().await;
            if let Some(cached) = &*cache {
                if Instant::now() < cached.expires_at {
                    return Ok(cached.token.clone());
                }
            }
        }

        self.fetch_and_cache_token(timeout_sec).await
    }

    async fn fetch_and_cache_token(&self, timeout_sec: u64) -> Result<String> {
        let params = [
            ("client_id", self.client_id.as_str()),
            ("client_secret", self.client_secret.as_str()),
            ("grant_type", "client_credentials"),
            ("scope", "public"),
        ];

        let resp = self.client
            .post("https://osu.ppy.sh/oauth/token")
            .form(&params)
            .timeout(Duration::from_secs(timeout_sec))
            .send()
            .await?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            anyhow::bail!("Token request failed: {} {}", status, text);
        }

        let data: TokenResponse = resp.json().await?;

        let expires_at = Instant::now()
            + Duration::from_secs(data.expires_in.saturating_sub(10));

        let token = data.access_token.clone();

        let mut cache = self.cached_token.lock().await;
        *cache = Some(CachedToken {
            token: token.clone(),
            expires_at,
        });

        Ok(token)
    }

    pub async fn invalidate_token(&self) {
        let mut cache = self.cached_token.lock().await;
        *cache = None;
    }

    pub async fn get_token_with_retry(
        &self,
        timeout_sec: u64,
        retries: u8,
    ) -> Option<String> {
        for attempt in 1..=retries {
            match self.get_token(timeout_sec).await {
                Ok(token) => return Some(token),
                Err(e) => {
                    eprintln!(
                        "Warning: token request failed (attempt {}): {}",
                        attempt, e
                    );
                    sleep(Duration::from_secs(2)).await;
                }
            }
        }

        None
    }

    pub async fn get_with_auth(
        &self,
        url: &str,
        timeout_sec: u64,
    ) -> Result<reqwest::Response> {
        let token = self.get_token(timeout_sec).await?;

        let resp = self.client
            .get(url)
            .bearer_auth(&token)
            .timeout(Duration::from_secs(timeout_sec))
            .send()
            .await?;

        if resp.status() == StatusCode::UNAUTHORIZED {
            self.invalidate_token().await;

            let new_token = self.get_token(timeout_sec).await?;

            let retry_resp = self.client
                .get(url)
                .bearer_auth(&new_token)
                .timeout(Duration::from_secs(timeout_sec))
                .send()
                .await?;

            return Ok(retry_resp);
        }

        Ok(resp)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_token_fetch() {
        let auth = OsuAuth::new();
        let token = auth.get_token_with_retry(10, 3).await;

        assert!(token.is_some());
        println!("Token obtained");
    }

    #[tokio::test]
    async fn test_authorized_request() {
        let auth = OsuAuth::new();

        let resp = auth
            .get_with_auth(
                "https://osu.ppy.sh/api/v2/users/peppy/osu",
                10,
            )
            .await
            .expect("Request failed");

        assert!(resp.status().is_success());

        let body = resp.text().await.unwrap();
        println!("Response body:\n{}", body);
    }

    #[tokio::test]
    async fn test_token_refresh_on_401() {
        let auth = OsuAuth::new();

        let first = auth.get_token(10).await.expect("first token");

        {
            let mut cache = auth.cached_token.lock().await;
            if let Some(cached) = cache.as_mut() {
                cached.token = "definitely_invalid_token".to_string();
            }
        }

        let resp = auth
            .get_with_auth(
                "https://osu.ppy.sh/api/v2/users/peppy/osu",
                10,
            )
            .await
            .expect("request");

        assert!(resp.status().is_success());

        let second = auth.get_token(10).await.expect("second token");

        assert_ne!(first, second, "token should be refreshed after 401");
    }
}
