use serde::Deserialize;



// куча unused !!!

#[allow(unused)]
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

#[allow(unused)]
#[derive(Debug, Deserialize)]
pub struct Poll {
    pub id: u64,
    pub question: String,
}

#[allow(unused)]
#[derive(Debug, Deserialize)]
pub struct Author {
    pub id: u64,
    pub username: String,
    pub avatar_url: Option<String>,
}

#[allow(unused)]
#[derive(Debug, Deserialize)]
pub struct ForumPostBody {
    pub raw: String,
    pub html: Option<String>,
}

#[allow(unused)]
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

#[allow(unused)]
#[derive(Debug, Deserialize)]
pub struct TopicResponse {
    pub topic: ForumTopic,
    pub posts: Vec<ForumPost>,
    pub cursor_string: Option<String>,
    pub sort: Option<String>,
}

#[allow(unused)]
#[derive(Debug, Deserialize)]
pub enum ForumError {
    PrivateForum,
    ApiError(String),
}