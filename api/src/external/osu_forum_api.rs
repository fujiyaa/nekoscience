use reqwest::Client;
use serde::Deserialize;
use anyhow::Result;

#[derive(Debug, Deserialize)]
pub struct ForumTopic {
    pub id: u64,
    pub forum_id: u64,
    pub user_id: u64,
    pub title: String,
    #[serde(rename = "type")]
    pub topic_type: String,
    pub created_at: Option<String>,
    pub updated_at: Option<String>,
    pub deleted_at: Option<String>,
    pub first_post_id: u64,
    pub last_post_id: u64,
    pub post_count: u64,
    pub views: u64,
    pub is_locked: bool,
    pub poll: Option<Poll>,
}

#[derive(Debug, Deserialize)]
pub struct Poll {
    pub id: u64,
    pub question: String,
}

#[derive(Debug, Deserialize)]
pub struct Author {
    pub id: u64,
    pub username: String,
    pub avatar_url: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct ForumPostBody {
    pub raw: String,
    pub html: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct ForumPost {
    pub topic_id: u64,
    pub author: Option<Author>,     //???
    pub user_id: u64,               // Author
    pub body: ForumPostBody,
    pub created_at: Option<String>,
    pub updated_at: Option<String>,
    pub edited_by_id: Option<u64>,
}

#[derive(Debug, Deserialize)]
pub struct TopicResponse {
    pub topic: ForumTopic,
    pub posts: Vec<ForumPost>,
    pub cursor_string: Option<String>,
    pub sort: Option<String>,
}

pub struct OsuApi {
    client: Client,
    pub token: String,
}

#[derive(Debug, Deserialize)]
pub enum ForumError {
    PrivateForum,
    ApiError(String),
}

impl OsuApi {
    pub fn new(token: impl Into<String>) -> Self {
        Self {
            client: Client::new(),
            token: token.into(),
        }
    }

    pub async fn get_topic(
        &self,
        topic_id: u64,
        sort: Option<&str>,
        limit: Option<u32>,
        start: Option<u64>,
        end: Option<u64>,
        cursor_string: Option<&str>,
    ) -> Result<Option<TopicResponse>, ForumError> {
        let url = format!("https://osu.ppy.sh/api/v2/forums/topics/{}", topic_id);

        let mut query_params: Vec<(&str, String)> = Vec::new();
        if let Some(sort) = sort { query_params.push(("sort", sort.to_string())); }
        if let Some(limit) = limit { query_params.push(("limit", limit.to_string())); }
        if let Some(start) = start { query_params.push(("start", start.to_string())); }
        if let Some(end) = end { query_params.push(("end", end.to_string())); }
        if let Some(cursor) = cursor_string { query_params.push(("cursor_string", cursor.to_string())); }

        let query_refs: Vec<(&str, &str)> = query_params.iter().map(|(k,v)| (*k, v.as_str())).collect();

        let req = self.client
            .get(&url)
            .query(&query_refs)
            .header("Authorization", format!("Bearer {}", self.token))
            .header("Accept", "application/json")
            .header("Content-Type", "application/json");

        let resp = req.send().await.map_err(|e| ForumError::ApiError(e.to_string()))?;
        let status = resp.status();
        let text = resp.text().await.map_err(|e| ForumError::ApiError(e.to_string()))?;

        if !status.is_success() {
            if status == reqwest::StatusCode::FORBIDDEN && text.contains("Only admin can view this forum") {
                return Ok(None); // Форум приватный — возвращаем None
            }

            // пытаемся вытащить error из JSON
            if let Ok(err_json) = serde_json::from_str::<serde_json::Value>(&text) {
                if let Some(err_msg) = err_json.get("error").and_then(|v| v.as_str()) {
                    return Err(ForumError::ApiError(err_msg.to_string()));
                }
            }

            return Err(ForumError::ApiError(format!("HTTP {}: {}", status, text)));
        }

        let topic_response: TopicResponse = serde_json::from_str(&text)
            .map_err(|e| ForumError::ApiError(e.to_string()))?;

        Ok(Some(topic_response))
    } 
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::external::osu_auth::OsuAuth;
    use anyhow::Result;

    async fn api() -> Result<OsuApi> {
        let auth = OsuAuth::new();
    
        let token = auth
            .get_token_with_retry(10, 3)
            .await
            .ok_or_else(|| anyhow::anyhow!("Failed to obtain Osu API token after 3 attempts"))?;

        Ok(OsuApi::new(token))
    }

    #[tokio::test]
    async fn test_get_topic() -> Result<()> {
        let api = api().await?;
        let topic_id = 2162676;
        match api.get_topic(topic_id, None, Some(5), None, None, None).await {
            Ok(Some(topic)) => {
                println!("Topic info: {:#?}", topic.topic);
                for (i, post) in topic.posts.iter().enumerate() {
                    println!("Post {}: {:#?}", i + 1, post);
                }
            }
            Ok(None) => eprintln!("Forum {} is private or restricted. Skipping test.", topic_id),
            Err(e) => return Err(anyhow::anyhow!("API error: {:?}", e)),
        }
        Ok(())
    }
}