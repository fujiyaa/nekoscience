use std::time::{SystemTime, UNIX_EPOCH, Duration};
use tokio::sync::Mutex;
use serde::Deserialize;
use anyhow::{Result};
use reqwest::Client;
use dotenv::dotenv;
use std::env;
use tokio::time::sleep;



// unused???
#[allow(unused)]
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
    cached_token: Mutex<Option<(String, u64)>>,
}

impl OsuAuth {
    pub fn new() -> Self {
        dotenv().ok();

        let osu_client_id = env::var("OSU_CLIENT_ID").expect("OSU_CLIENT_ID not set");
        let osu_client_secret = env::var("OSU_CLIENT_SECRET").expect("OSU_CLIENT_SECRET not set");
        

        Self {
            client_id: osu_client_id,
            client_secret: osu_client_secret,
            client: Client::new(),
            cached_token: Mutex::new(None),
        }
    }

    pub async fn get_token(&self, timeout_sec: u64) -> Result<String> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();

        {
            let cache = self.cached_token.lock().await;
            if let Some((token, expiry)) = &*cache {
                if now < *expiry {
                    return Ok(token.clone());
                }
            }
        }

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
            anyhow::bail!("Token request failed with status {}: {}", status, text);
        }

        let data: TokenResponse = resp.json().await?;
        let expiry = now + data.expires_in - 5;

        {
            let mut cache = self.cached_token.lock().await;
            *cache = Some((data.access_token.clone(), expiry));
        }

        Ok(data.access_token)
    }

    pub async fn get_token_with_retry(&self, timeout_sec: u64, retries: u8) -> Option<String> {
        let mut attempts = 0;
        loop {
            attempts += 1;
            match self.get_token(timeout_sec).await {
                Ok(token) => return Some(token),
                Err(e) => {
                    if attempts >= retries {
                        eprintln!("Warning: failed to get token after {} attempts: {}", attempts, e);
                        return None;
                    }
                    eprintln!("Warning: token request failed (attempt {}): {}. Retrying...", attempts, e);
                    sleep(std::time::Duration::from_secs(2)).await;
                }
            }
        }
    }
}



#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_get_token() {
        let auth = OsuAuth::new();
        let token = auth.get_token_with_retry(10, 3).await;

        match token {
            Some(token) => println!("Token: {}", token),
            None => eprintln!("Token not obtained, continuing without it."),
        }
    }
}
